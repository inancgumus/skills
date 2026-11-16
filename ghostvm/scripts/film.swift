import AppKit
import AVFoundation
import Foundation
import ScreenCaptureKit

// film OUT.mov MAX-SECONDS [--app NAME] [--rect x,y,w,h] [--1x] [--stop FILE] [--tick FILE] [--codec lossless|hevc] [--mbps N]
// Records the guest screen at the display's refresh rate (60 fps), 2x pixels by default, as ProRes 4444 (matches a
// 2x screenshot exactly, about 30 MB per second of motion), or HEVC with --codec hevc (about 0.3 MB/s, slightly soft).
// --app crops to the app's largest window. --rect crops to a rectangle in guest screen points (a `shot` pixel).
// Window-only capture runs at about 30 fps, so this always captures the display and crops it.
// Stops when FILE appears, on SIGTERM, or after MAX-SECONDS.
// --tick FILE: touches FILE whenever the picture really changes. It compares every pixel of the areas
// ScreenCaptureKit reports as redrawn with the previous frame, so even a 1 pt change counts and a redraw with
// the same pixels does not.
// Prints "recording <epoch ms>" when the first frame is written and "saved <path> <epoch ms>" at the end.

// Writes every frame ScreenCaptureKit delivers (it delivers one only when pixels change) into the file, and touches
// the tick file when the pixels really changed. --tick compares every pixel of the areas ScreenCaptureKit reports as
// redrawn with the previous frame, so even a 1 pt change counts and a redraw with the same pixels does not.
final class Writer: NSObject, SCStreamOutput, @unchecked Sendable {
    let writer: AVAssetWriter
    let input: AVAssetWriterInput
    let tick: String?
    let lock = NSLock()
    var started = false, stopped = false, dropped = 0, frames = 0
    var previous: CVPixelBuffer?
    var onStart: (() -> Void)?
    init(url: URL, width: Int, height: Int, codec: String, bitrate: Int, tick: String?) throws {
        writer = try AVAssetWriter(outputURL: url, fileType: url.pathExtension.lowercased() == "mp4" ? .mp4 : .mov)
        var settings: [String: Any] = [AVVideoWidthKey: width, AVVideoHeightKey: height]
        // No color tags: tagged files decode with shifted colors (measured). ProRes 4444 matches a 2x PNG exactly.
        if codec == "lossless" {
            settings[AVVideoCodecKey] = AVVideoCodecType.proRes4444
        } else {
            settings[AVVideoCodecKey] = AVVideoCodecType.hevc
            settings[AVVideoCompressionPropertiesKey] = (bitrate == 0 ? [AVVideoQualityKey: 1.0] : [AVVideoAverageBitRateKey: bitrate]).merging([AVVideoExpectedSourceFrameRateKey: 60, AVVideoAllowFrameReorderingKey: false] as [String: Any]) { a, _ in a }
        }
        input = AVAssetWriterInput(mediaType: .video, outputSettings: settings)
        input.expectsMediaDataInRealTime = true
        writer.add(input)
        self.tick = tick
        if let tick { FileManager.default.createFile(atPath: tick, contents: nil) }
    }
    func stream(_ stream: SCStream, didOutputSampleBuffer buffer: CMSampleBuffer, of type: SCStreamOutputType) {
        guard type == .screen, buffer.isValid,
              let info = (CMSampleBufferGetSampleAttachmentsArray(buffer, createIfNecessary: false) as? [[SCStreamFrameInfo: Any]])?.first,
              let raw = info[.status] as? Int, SCFrameStatus(rawValue: raw) == .complete,
              let pixels = CMSampleBufferGetImageBuffer(buffer) else { return }
        lock.lock(); defer { lock.unlock() }
        if stopped { return }
        if !started {
            guard writer.startWriting() else { return }
            writer.startSession(atSourceTime: buffer.presentationTimeStamp)
            started = true
            onStart?()
        }
        if input.isReadyForMoreMediaData { input.append(buffer); frames += 1 } else { dropped += 1 }
        if let tick {
            let dirty = (info[.dirtyRects] as? [NSDictionary] ?? []).compactMap { CGRect(dictionaryRepresentation: $0 as CFDictionary) }
            if debug { FileHandle.standardError.write("frame \(CVPixelBufferGetWidth(pixels))x\(CVPixelBufferGetHeight(pixels)) dirty \(dirty)\n".data(using: .utf8)!) }
            if let previous, CVPixelBufferGetWidth(previous) == CVPixelBufferGetWidth(pixels), CVPixelBufferGetHeight(previous) == CVPixelBufferGetHeight(pixels) {
                if differs(pixels, previous, in: dirty.isEmpty ? [CGRect(x: 0, y: 0, width: CVPixelBufferGetWidth(pixels), height: CVPixelBufferGetHeight(pixels))] : dirty) { utimes(tick, nil) }
            } else { utimes(tick, nil) }
            previous = pixels
        }
    }
    func finish() async -> (frames: Int, dropped: Int) {
        let now = CMClockGetTime(CMClockGetHostTimeClock())
        let wasStarted: Bool = lock.withLock { stopped = true; return started }
        if wasStarted {
            writer.endSession(atSourceTime: now)
            input.markAsFinished()
            await writer.finishWriting()
        }
        return lock.withLock { (frames, dropped) }
    }
    func differs(_ a: CVPixelBuffer, _ b: CVPixelBuffer, in rects: [CGRect]) -> Bool {
        CVPixelBufferLockBaseAddress(a, .readOnly); CVPixelBufferLockBaseAddress(b, .readOnly)
        defer { CVPixelBufferUnlockBaseAddress(a, .readOnly); CVPixelBufferUnlockBaseAddress(b, .readOnly) }
        guard let pa = CVPixelBufferGetBaseAddress(a), let pb = CVPixelBufferGetBaseAddress(b) else { return true }
        let ra = CVPixelBufferGetBytesPerRow(a), rb = CVPixelBufferGetBytesPerRow(b)
        let width = CVPixelBufferGetWidth(a), height = CVPixelBufferGetHeight(a)
        for rect in rects {
            let r = rect.integral.intersection(CGRect(x: 0, y: 0, width: width, height: height))
            if r.isEmpty { continue }
            let x = Int(r.minX) * 4, bytes = Int(r.width) * 4
            for y in Int(r.minY)..<Int(r.maxY) where memcmp(pa + y * ra + x, pb + y * rb + x, bytes) != 0 { return true }
        }
        return false
    }
}

func now() -> Int { Int(Date().timeIntervalSince1970 * 1000) }
let args = Array(CommandLine.arguments.dropFirst())
func option(_ name: String) -> String? { args.firstIndex(of: name).flatMap { $0 + 1 < args.count ? args[$0 + 1] : nil } }
guard args.count >= 2, let limit = Double(args[1]) else {
    print("usage: film OUT.mov MAX-SECONDS [--app NAME] [--rect x,y,w,h] [--1x] [--stop FILE]"); exit(2)
}
let out = URL(fileURLWithPath: args[0])
let stop = option("--stop")
let rect = option("--rect").map { $0.split(separator: ",").compactMap { Double($0) } }
let app = option("--app")?.lowercased()
let tick = option("--tick")
let debug = ProcessInfo.processInfo.environment["FILM_DEBUG"] != nil
let codec = option("--codec") ?? "lossless"
let bitrate = Int(option("--mbps") ?? "40").map { $0 * 1_000_000 } ?? 40_000_000
var stopped = false
signal(SIGTERM, SIG_IGN)
let term = DispatchSource.makeSignalSource(signal: SIGTERM, queue: .main)
term.setEventHandler { stopped = true }
term.resume()
try? FileManager.default.removeItem(at: out)

func fail(_ message: String) -> Never { print("film: \(message)"); fflush(stdout); exit(1) }

Task { @MainActor in
    do {
        let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)
        guard let display = content.displays.first else { fail("no display") }
        let screen = CGRect(x: 0, y: 0, width: display.width, height: display.height)
        var area = screen
        if let app {
            let windows = content.windows.filter { $0.owningApplication?.applicationName.lowercased() == app && $0.isOnScreen && $0.windowLayer == 0 }
            guard let window = windows.max(by: { $0.frame.width * $0.frame.height < $1.frame.width * $1.frame.height }) else {
                fail("no on-screen window for app \"\(option("--app")!)\". Run vmx apps.")
            }
            area = window.frame.offsetBy(dx: -display.frame.minX, dy: -display.frame.minY)
        }
        if let rect {
            guard rect.count == 4 else { fail("--rect needs x,y,w,h") }
            area = CGRect(x: rect[0], y: rect[1], width: rect[2], height: rect[3])
        }
        area = area.intersection(screen).integral
        guard area.width >= 16, area.height >= 16 else { fail("the area to record is off screen or too small: \(area)") }
        let config = SCStreamConfiguration()
        if area != screen { config.sourceRect = area }
        // The display's real pixels per point (2 on Retina), unless --1x.
        let mode = CGDisplayCopyDisplayMode(display.displayID)
        let native = mode.map { max(1, $0.pixelWidth / max(1, $0.width)) } ?? 2
        let scale = args.contains("--1x") ? 1 : native
        config.width = Int(area.width) * scale / 2 * 2
        config.height = Int(area.height) * scale / 2 * 2
        config.minimumFrameInterval = CMTime(value: 1, timescale: 60)
        config.showsCursor = false
        config.queueDepth = 8
        config.pixelFormat = kCVPixelFormatType_32BGRA
        let output = try Writer(url: out, width: config.width, height: config.height, codec: codec, bitrate: bitrate, tick: tick)
        let stream = SCStream(filter: SCContentFilter(display: display, excludingWindows: []), configuration: config, delegate: nil)
        try stream.addStreamOutput(output, type: .screen, sampleHandlerQueue: DispatchQueue(label: "frames", qos: .userInteractive))
        try await withCheckedThrowingContinuation { (c: CheckedContinuation<Void, Error>) in
            output.onStart = { c.resume() }
            stream.startCapture { error in if let error { output.onStart = nil; c.resume(throwing: error) } }
        }
        // The recorded area in screen points, so frames and pixels can take screen points too.
        print("recording \(now()) \(config.width)x\(config.height) \(Int(area.minX)),\(Int(area.minY)),\(Int(area.width)),\(Int(area.height))"); fflush(stdout)
        let deadline = Date().addingTimeInterval(limit)
        while !stopped && Date() < deadline && !(stop.map { FileManager.default.fileExists(atPath: $0) } ?? false) {
            try await Task.sleep(for: .milliseconds(10))
        }
        if !stopped && Date() >= deadline { print("film: warning: stopped at the \(Int(limit)) s limit; later actions are not in the film") }
        try? await stream.stopCapture()
        let result = await output.finish()
        if result.dropped > 0 { print("film: warning: the encoder dropped \(result.dropped) of \(result.frames + result.dropped) frames") }
        print("saved \(out.path) \(now())"); fflush(stdout)
        exit(0)
    } catch {
        fail("\(error)")
    }
}
// ScreenCaptureKit adds a menu bar item while recording, which needs a running AppKit main thread.
let application = NSApplication.shared
application.setActivationPolicy(.prohibited)
application.run()
