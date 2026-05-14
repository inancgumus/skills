# Good Real-Life Split Example: Browser Frame Document Race

Issue: `#4371`  
Goal: split one broad race fix into reviewable, atomic commits.

## Large diff before split (input)

This is the kind of mixed large diff that should be split.

```diff
diff --git a/internal/js/modules/k6/browser/common/frame.go b/internal/js/modules/k6/browser/common/frame.go
@@ -27,6 +27,10 @@ type DocumentInfo struct {
 	request    *Request
 }
 
+func (d *DocumentInfo) is(id string) bool {
+	return d != nil && d.documentID == id
+}
+
 @@ -110,9 +114,9 @@ type Frame struct {
-	currentDocument   *DocumentInfo
-	pendingDocumentMu sync.RWMutex
-	pendingDocument   *DocumentInfo
+	currentDocument *DocumentInfo
+	pendingDocument *DocumentInfo
+	documentMu      sync.RWMutex
 @@ -313,6 +317,36 @@ func (f *Frame) hasLifecycleEventFired(event LifecycleEvent) bool {
+func (f *Frame) requestByDocumentID(id string) *Request { ... }
+func (f *Frame) responseByDocumentID(id string) *Response { ... }
 @@ -2098,7 +2132,7 @@ func (f *Frame) WaitForNavigation(...){
-		resp       *Response
+		docID      string
 @@ -2115,13 +2149,8 @@
-			req := e.newDocument.request
-			if req != nil {
-				req.responseMu.RLock()
-				resp = req.response
-				req.responseMu.RUnlock()
-			}
+			docID = e.newDocument.documentID
 @@ -2138,6 +2167,11 @@
+	var resp *Response
+	if !sameDocNav {
+		resp = f.responseByDocumentID(docID)
+	}
 
 diff --git a/internal/js/modules/k6/browser/common/frame_manager.go b/internal/js/modules/k6/browser/common/frame_manager.go
@@ -102,14 +102,14 @@
-	frame.pendingDocumentMu.Lock()
+	frame.documentMu.Lock()
@@ -298,8 +298,8 @@
-	frame.pendingDocumentMu.Lock()
-	defer frame.pendingDocumentMu.Unlock()
+	frame.documentMu.Lock()
+	defer frame.documentMu.Unlock()
@@ -400,10 +400,10 @@
-	if frame.pendingDocument != nil && frame.pendingDocument.documentID == documentID {
+	if frame.pendingDocument.is(documentID) {
@@ -531,9 +531,19 @@
-		frame.pendingDocument = &DocumentInfo{documentID: req.documentID, request: req}
+		switch {
+		case frame.currentDocument.is(req.documentID):
+			frame.currentDocument.request = req
+			if frame.pendingDocument.is(req.documentID) {
+				frame.pendingDocument = nil
+			}
+		case frame.pendingDocument.is(req.documentID):
+			frame.pendingDocument.request = req
+		default:
+			frame.pendingDocument = &DocumentInfo{documentID: req.documentID, request: req}
+		}
@@ -720,7 +730,7 @@
-	var resp *Response
+	var docID string
@@ -728,12 +738,8 @@
-			req := e.newDocument.request
-			if req != nil {
-				req.responseMu.RLock()
-				resp = req.response
-				req.responseMu.RUnlock()
-			}
+			if e.newDocument != nil {
+				docID = e.newDocument.documentID
+			}
@@ -746,7 +752,7 @@
-	return resp, nil
+	return frame.responseByDocumentID(docID), nil
```

## Atomic commits after split (output)

### 1) `browser: rename frame document mutex`

Original commit message:

```text
browser: rename frame document mutex
This lock protects both current and pending document state.
The old name suggested it only covered pending state.
```

Why this was split this way for the agent:
This is pure rename-only churn with no behavior change. Keeping it alone makes
every later diff smaller and easier to reason about.

```diff
@@ -110,9 +110,9 @@ type Frame struct {
-	currentDocument   *DocumentInfo
-	pendingDocumentMu sync.RWMutex
-	pendingDocument   *DocumentInfo
+	currentDocument *DocumentInfo
+	pendingDocument *DocumentInfo
+	documentMu      sync.RWMutex
@@
-	frame.pendingDocumentMu.Lock()
+	frame.documentMu.Lock()
```

### 2) `browser: add document id matcher`

Original commit message:

```text
browser: add document id matcher
There were repeated nil checks around document comparisons.
A small matcher keeps those checks consistent.
```

Why this was split this way for the agent:
This introduces one tiny primitive (`DocumentInfo.is`) and nothing else. It is
cheap to review and creates a reusable building block for later commits.

```diff
@@ -27,6 +27,10 @@ type DocumentInfo struct {
 	request    *Request
 }
 
+func (d *DocumentInfo) is(id string) bool {
+	return d != nil && d.documentID == id
+}
@@
-	if frame.pendingDocument != nil && frame.pendingDocument.documentID == documentID {
+	if frame.pendingDocument.is(documentID) {
```

### 3) `browser: add frame request lookup`

Original commit message:

```text
browser: add frame request lookup
Request lookup by document ID was scattered and easy to get wrong.
Putting it behind one helper keeps that logic in one place.
```

Why this was split this way for the agent:
Only request lookup logic is introduced here. Isolating it prevents helper
creation from being mixed with the later behavior-ordering change.

```diff
@@ -317,6 +317,24 @@ func (f *Frame) hasLifecycleEventFired(event LifecycleEvent) bool {
+func (f *Frame) requestByDocumentID(id string) *Request {
+	if id == "" {
+		return nil
+	}
+	...
+}
@@
-			req := e.newDocument.request
+			request = frame.requestByDocumentID(e.newDocument.documentID)
```

### 4) `browser: add frame response lookup`

Original commit message:

```text
browser: add frame response lookup
Response lookup should follow the same path as request lookup.
A dedicated helper keeps request/response access aligned.
```

Why this was split this way for the agent:
This keeps response access policy in one helper, separate from call-order
changes. The reviewer can confirm symmetry with request lookup in one commit.

```diff
@@ -335,6 +335,18 @@ func (f *Frame) requestByDocumentID(id string) *Request {
+func (f *Frame) responseByDocumentID(id string) *Response {
+	request := f.requestByDocumentID(id)
+	if request == nil {
+		return nil
+	}
+	...
+}
@@
-				request.responseMu.RLock()
-				resp = request.response
-				request.responseMu.RUnlock()
+				resp = frame.responseByDocumentID(e.newDocument.documentID)
```

### 5) `browser: move goto response after lifecycle`

Original commit message:

```text
browser: move goto response after lifecycle
The response could be read before network handling caught up.
Waiting for lifecycle first removes that timing window.
```

Why this was split this way for the agent:
This is one behavior change in one path (`Goto` via `NavigateFrame`). Isolated
ordering changes are easier to test and easier to roll back.

```diff
@@
-	var resp *Response
+	var docID string
@@
-				resp = frame.responseByDocumentID(e.newDocument.documentID)
+				docID = e.newDocument.documentID
@@
-	return resp, nil
+	return frame.responseByDocumentID(docID), nil
```

### 6) `browser: move waitnav response after lifecycle`

Original commit message:

```text
browser: move waitnav response after lifecycle
WaitForNavigation had the same ordering problem as Goto.
Applying the same ordering keeps both paths consistent.
```

Why this was split this way for the agent:
This applies the same behavior rule to a second caller path only. Keeping it
separate avoids conflating two API contracts in one commit.

```diff
@@
-		resp       *Response
+		docID      string
@@
-			req := e.newDocument.request
-			...
-			resp = req.response
+			docID = e.newDocument.documentID
@@
+	var resp *Response
+	if !sameDocNav {
+		resp = f.responseByDocumentID(docID)
+	}
```

### 7) `browser: rebind request to matching doc`

Original commit message:

```text
browser: rebind request to matching doc
During redirects, requests can land on current or pending documents.
Rebinding by document ID keeps the association correct.
```

Why this was split this way for the agent:
This mutates document/request state transitions and is logically distinct from
response-read ordering, so it stays in its own final fix commit.

```diff
@@
-		frame.pendingDocument = &DocumentInfo{documentID: req.documentID, request: req}
+		switch {
+		case frame.currentDocument.is(req.documentID):
+			frame.currentDocument.request = req
+			if frame.pendingDocument.is(req.documentID) {
+				frame.pendingDocument = nil
+			}
+		case frame.pendingDocument.is(req.documentID):
+			frame.pendingDocument.request = req
+		default:
+			frame.pendingDocument = &DocumentInfo{documentID: req.documentID, request: req}
+		}
```

## Why this reference is useful

It shows one large mixed diff first, then the exact atomic split shape:
rename, matcher helper, request helper, response helper, two separate behavior
moves, and one state-fix commit.

Each commit is independently kept clean with `make lint` and `gofmt`.
