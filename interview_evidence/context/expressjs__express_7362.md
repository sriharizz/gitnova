# Issue Context Dossier: `expressjs/express` #7362

**Title:** res.send(ArrayBuffer) silently sends {} as JSON  
**Repository:** https://github.com/expressjs/express  
**Language:** JavaScript  
**Suitability Score:** 67/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `CHECK_DISCUSSION`  

---

## 1. Problem Summary & Objective
> When a developer passes a raw ArrayBuffer to res.send(), Express treats it as a generic object and serializes it to an empty JSON object '{}' instead of sending it as binary data.

## 2. Root Cause Analysis
> In lib/response.js, the 'object' type check only checks ArrayBuffer.isView(chunk) to identify binary views (like Uint8Array). It lacks a check for raw 'ArrayBuffer' instances (e.g., chunk instanceof ArrayBuffer). Consequently, raw ArrayBuffers fall through to the JSON serialization logic, resulting in an empty JSON object response.

## 3. Grounded Code Locations & Citations
- File: `lib/response.js` (Lines: `141-160`) | Symbol: `res.send` | Role: *Type checking and handling of response chunk* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect res.send in lib/response.js**: Inspect the res.send method in lib/response.js and locate the switch (typeof chunk) block. Identify where ArrayBuffer.isView(chunk) is used to handle binary views. (Target: `lib/response.js`)
2. **Add ArrayBuffer Instance Check**: Modify the condition in the object case of res.send to check if chunk is an instance of ArrayBuffer (using chunk instanceof ArrayBuffer). If it is, convert it to a Node.js Buffer using Buffer.from(chunk) and set the content type to binary using this.type('bin') before sending. (Target: `lib/response.js`)
3. **Add Regression Tests in test/res.send.js**: Add a new test suite or test case in test/res.send.js that calls res.send(new ArrayBuffer(10)) and asserts that the response has the 'Content-Type' header set to 'application/octet-stream' and contains the correct binary payload. (Target: `test/res.send.js`)
4. **Run Tests and Verify**: Execute the test suite using the command npm test to verify that the new test passes and no regressions are introduced in other response-sending behaviors. (Target: `None`)

## 5. Educational Concepts
### ArrayBuffer vs ArrayBuffer Views
- **What is it:** An ArrayBuffer represents a generic, fixed-length raw binary data buffer. ArrayBuffer.isView() returns true only for views like TypedArrays (e.g., Uint8Array) or DataView, but false for the raw ArrayBuffer itself.
- **Why it matters:** Developers need to understand this distinction because APIs handling binary data must check for both the raw buffer container and its views to correctly process binary payloads.
- **Connection to Issue:** The bug occurs because the code only checks ArrayBuffer.isView(chunk), completely missing raw ArrayBuffer instances and letting them fall through to JSON serialization.

### Node.js Buffer from ArrayBuffer
- **What is it:** Node.js Buffers can be created directly from an ArrayBuffer using Buffer.from(arrayBuffer), which shares the same allocated memory without copying.
- **Why it matters:** This allows efficient conversion of standard web binary types (ArrayBuffer) into Node.js-native binary types (Buffer) for network transmission.
- **Connection to Issue:** Once the ArrayBuffer is correctly identified, the existing fallback logic in res.send() will automatically convert it to a Buffer using Buffer.from(chunk) and calculate its correct byte length.

