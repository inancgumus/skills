import AppKit
import AVFoundation
import Compression
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
    // --codec none keeps no film (only the tick file). --codec raw writes tight BGRA frames to OUT and their times
    // in seconds to OUT.times, without VideoToolbox, for the host to encode. Both work when the guest encoder hangs.
    let writer: AVAssetWriter?
    let input: AVAssetWriterInput?
    let raw: FileHandle?
    let rawQueue = DispatchQueue(label: "raw")
    var pending = 0
    let tick: String?
    let lock = NSLock()
    var started = false, stopped = false, dropped = 0, frames = 0
    var previous: CVPixelBuffer?
    var onStart: (() -> Void)?
    init(url: URL, width: Int, height: Int, codec: String, bitrate: Int, tick: String?) throws {
        self.tick = tick
        if let tick { FileManager.default.createFile(atPath: tick, contents: nil) }
        if codec == "none" || codec == "raw" {
            writer = nil; input = nil
            if codec == "raw" {
                FileManager.default.createFile(atPath: url.path, contents: nil); raw = try FileHandle(forWritingTo: url)
                var h = Data("VMXF".utf8); h.append(le(UInt32(width))); h.append(le(UInt32(height))); raw!.write(h)
            } else { raw = nil }
            super.init(); return
        }
        raw = nil
        let writer = try AVAssetWriter(outputURL: url, fileType: url.pathExtension.lowercased() == "mp4" ? .mp4 : .mov)
        var settings: [String: Any] = [AVVideoWidthKey: width, AVVideoHeightKey: height]
        // No color tags: tagged files decode with shifted colors (measured). ProRes 4444 matches a 2x PNG exactly.
        if codec == "lossless" {
            settings[AVVideoCodecKey] = AVVideoCodecType.proRes4444
        } else {
            settings[AVVideoCodecKey] = AVVideoCodecType.hevc
            settings[AVVideoCompressionPropertiesKey] = (bitrate == 0 ? [AVVideoQualityKey: 1.0] : [AVVideoAverageBitRateKey: bitrate]).merging([AVVideoExpectedSourceFrameRateKey: 60, AVVideoAllowFrameReorderingKey: false] as [String: Any]) { a, _ in a }
        }
        let input = AVAssetWriterInput(mediaType: .video, outputSettings: settings)
        input.expectsMediaDataInRealTime = true
        writer.add(input)
        self.writer = writer; self.input = input
        super.init()
    }
    // Copies the frame's rows without padding and writes them on a serial queue; drops a frame when 32 wait.
    func appendRaw(_ pixels: CVPixelBuffer, _ t: CMTime) {
        guard let raw else { return }
        if pending >= 32 { dropped += 1; return }
        CVPixelBufferLockBaseAddress(pixels, .readOnly)
        let w = CVPixelBufferGetWidth(pixels), h = CVPixelBufferGetHeight(pixels), row = CVPixelBufferGetBytesPerRow(pixels)
        var data = Data(count: w * h * 4)
        if let base = CVPixelBufferGetBaseAddress(pixels) {
            data.withUnsafeMutableBytes { d in for y in 0..<h { memcpy(d.baseAddress! + y * w * 4, base + y * row, w * 4) } }
        }
        CVPixelBufferUnlockBaseAddress(pixels, .readOnly)
        frames += 1; pending += 1
        rawQueue.async {
            // One record per frame: pts in seconds (Float64), then the LZ4 block's size and bytes (size 0: stored as is).
            var rec = Data(); rec.append(le(t.seconds.bitPattern))
            var packed = Data(count: data.count)
            let n = packed.withUnsafeMutableBytes { d in data.withUnsafeBytes { s in
                compression_encode_buffer(d.bindMemory(to: UInt8.self).baseAddress!, data.count, s.bindMemory(to: UInt8.self).baseAddress!, data.count, nil, COMPRESSION_LZ4_RAW) } }
            if n > 0 { rec.append(le(UInt32(n))); rec.append(packed.prefix(n)) } else { rec.append(le(UInt32(0))); rec.append(data) }
            raw.write(rec)
            self.lock.withLock { self.pending -= 1 }
        }
    }
    func stream(_ stream: SCStream, didOutputSampleBuffer buffer: CMSampleBuffer, of type: SCStreamOutputType) {
        guard type == .screen, buffer.isValid,
              let info = (CMSampleBufferGetSampleAttachmentsArray(buffer, createIfNecessary: false) as? [[SCStreamFrameInfo: Any]])?.first,
              let raw = info[.status] as? Int, SCFrameStatus(rawValue: raw) == .complete,
              let pixels = CMSampleBufferGetImageBuffer(buffer) else { return }
        lock.lock(); defer { lock.unlock() }
        if stopped { return }
        if !started {
            if let writer {
                guard writer.startWriting() else { return }
                writer.startSession(atSourceTime: buffer.presentationTimeStamp)
            }
            started = true
            onStart?()
        }
        if let input { if input.isReadyForMoreMediaData { input.append(buffer); frames += 1 } else { dropped += 1 } }
        else if raw != nil { appendRaw(pixels, buffer.presentationTimeStamp) } else { frames += 1 }
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
        if wasStarted, let writer, let input {
            writer.endSession(atSourceTime: now)
            input.markAsFinished()
            await writer.finishWriting()
        }
        if let raw { rawQueue.sync { try? raw.close() } }
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

func le<T: FixedWidthInteger>(_ v: T) -> Data { withUnsafeBytes(of: v.littleEndian) { Data($0) } }

// film --encode IN.frames OUT.mov|OUT.mp4: on the host, turns the guest's raw frames into a film with each frame's own
// time (ProRes 4444 in .mov, HEVC in .mp4), so the guest never needs its video encoder.
func encode(_ inPath: String, _ outPath: String) -> Never {
    func die(_ m: String) -> Never { print("film: \(m)"); exit(1) }
    guard let fh = FileHandle(forReadingAtPath: inPath) else { die("no frames at \(inPath)") }
    func read<T: FixedWidthInteger>(_: T.Type) -> T? { let d = fh.readData(ofLength: MemoryLayout<T>.size); return d.count == MemoryLayout<T>.size ? d.withUnsafeBytes { T(littleEndian: $0.loadUnaligned(as: T.self)) } : nil }
    guard fh.readData(ofLength: 4) == Data("VMXF".utf8), let w32 = read(UInt32.self), let h32 = read(UInt32.self) else { die("\(inPath) is not a frames file") }
    let w = Int(w32), h = Int(h32)
    let url = URL(fileURLWithPath: outPath); try? FileManager.default.removeItem(at: url)
    let mp4 = url.pathExtension.lowercased() == "mp4"
    guard let writer = try? AVAssetWriter(outputURL: url, fileType: mp4 ? .mp4 : .mov) else { die("cannot write \(outPath)") }
    var settings: [String: Any] = [AVVideoWidthKey: w, AVVideoHeightKey: h, AVVideoCodecKey: mp4 ? AVVideoCodecType.hevc : AVVideoCodecType.proRes4444]
    if mp4 { settings[AVVideoCompressionPropertiesKey] = [AVVideoQualityKey: 1.0, AVVideoAllowFrameReorderingKey: false] }
    let input = AVAssetWriterInput(mediaType: .video, outputSettings: settings)
    let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA, kCVPixelBufferWidthKey as String: w, kCVPixelBufferHeightKey as String: h])
    writer.add(input)
    guard writer.startWriting() else { die("cannot start \(outPath): \(writer.error.map { "\($0)" } ?? "")") }
    var first: Double?, last = 0.0, n = 0
    while let bits = read(UInt64.self), let size = read(UInt32.self) {
        let t = Double(bitPattern: bits)
        let body = fh.readData(ofLength: size == 0 ? w * h * 4 : Int(size))
        if first == nil { first = t; writer.startSession(atSourceTime: .zero) }
        var pb: CVPixelBuffer?
        guard let pool = adaptor.pixelBufferPool, CVPixelBufferPoolCreatePixelBuffer(nil, pool, &pb) == kCVReturnSuccess, let pb else { die("no pixel buffer") }
        CVPixelBufferLockBaseAddress(pb, [])
        let base = CVPixelBufferGetBaseAddress(pb)!, row = CVPixelBufferGetBytesPerRow(pb)
        var plain = Data(count: w * h * 4)
        if size == 0 { plain = body } else {
            let got = plain.withUnsafeMutableBytes { d in body.withUnsafeBytes { s in compression_decode_buffer(d.bindMemory(to: UInt8.self).baseAddress!, w * h * 4, s.bindMemory(to: UInt8.self).baseAddress!, body.count, nil, COMPRESSION_LZ4_RAW) } }
            guard got == w * h * 4 else { die("frame \(n) is damaged") }
        }
        plain.withUnsafeBytes { s in for y in 0..<h { memcpy(base + y * row, s.baseAddress! + y * w * 4, w * 4) } }
        CVPixelBufferUnlockBaseAddress(pb, [])
        while !input.isReadyForMoreMediaData { usleep(1000) }
        last = t - first!
        guard adaptor.append(pb, withPresentationTime: CMTime(seconds: last, preferredTimescale: 600_000)) else { die("cannot add frame \(n)") }
        n += 1
    }
    guard n > 0 else { die("no frames in \(inPath)") }
    writer.endSession(atSourceTime: CMTime(seconds: last + 1.0 / 60, preferredTimescale: 600_000))
    input.markAsFinished()
    let done = DispatchSemaphore(value: 0)
    writer.finishWriting { done.signal() }
    done.wait()
    guard writer.status == .completed else { die("could not finish \(outPath): \(writer.error.map { "\($0)" } ?? "")") }
    print("encoded \(n) frames"); exit(0)
}
if CommandLine.arguments.count == 4, CommandLine.arguments[1] == "--encode" { encode(CommandLine.arguments[2], CommandLine.arguments[3]) }

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
