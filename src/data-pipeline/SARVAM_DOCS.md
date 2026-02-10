```
***

title: Document Intelligence Overview
description: >-
Transform documents into structured, queryable data with Sarvam's Document
Intelligence API. Powered by Sarvam Vision for accurate text extraction and
table parsing across 23 languages (22 Indian + English).
icon: file-lines
canonical-url: '[https://docs.sarvam.ai/api-reference-docs/document-intelligence/overview](https://docs.sarvam.ai/api-reference-docs/document-intelligence/overview)'
'og:title': Document Intelligence API - Sarvam AI
'og:description': >-
Transform PDFs into structured data with Sarvam's Document Intelligence API.
Powered by Sarvam Vision for 23 languages (22 Indian + English) with table
extraction.
'og:type': article
'og:site\_name': Sarvam AI Developer Documentation
'og:image':
type: url
value: >-
[https://res.cloudinary.com/dvcb20x9a/image/upload/v1743510800/image\_3\_rpnrug.png](https://res.cloudinary.com/dvcb20x9a/image/upload/v1743510800/image_3_rpnrug.png)
'og:image:width': 1200
'og:image:height': 630
'twitter:card': summary\_large\_image
'twitter:title': Document Intelligence API - Sarvam AI
'twitter:description': >-
Transform PDFs into structured data with Sarvam's Document Intelligence API.
Powered by Sarvam Vision for 23 languages (22 Indian + English) with table
extraction.
'twitter:image':
type: url
value: >-
[https://res.cloudinary.com/dvcb20x9a/image/upload/v1743510800/image\_3\_rpnrug.png](https://res.cloudinary.com/dvcb20x9a/image/upload/v1743510800/image_3_rpnrug.png)
'twitter:site': '@SarvamAI'
---------------------------

Sarvam's Document Intelligence API provides enterprise-grade document processing powered by [Sarvam Vision](/api-reference-docs/getting-started/models/sarvam-vision), our state-of-the-art multimodal model.

<p>
  Transform any document into structured, searchable, and machine-readable data with world-class accuracy.
</p>

<CardGroup cols={2}>
  <Card title="Sarvam Vision" icon="eye" href="/api-reference-docs/getting-started/models/sarvam-vision">
    Our 3B parameter multimodal model powering Document Intelligence. SOTA performance on global and Indic benchmarks.
  </Card>
</CardGroup>

***

## What is Document Intelligence?

Document Intelligence is a comprehensive document processing pipeline powered by Sarvam Vision that:

1. **Extracts Text**: High-fidelity text extraction across 23 languages (22 Indian + English)
2. **Preserves Structure**: Maintains document layout, reading order, and hierarchies
3. **Parses Tables**: Transforms tables into structured HTML or Markdown formats
4. **Outputs Structured Data**: Generates clean, machine-readable HTML or Markdown output

***

## Key Features

<CardGroup cols={2}>
  <Card title="23 Language Support" icon="language">
    Native support for all Constitutionally recognized Indian languages and English with script-native accuracy.
  </Card>

  <Card title="Multiple Output Formats" icon="code">
    Export to HTML or Markdown files, delivered as a ZIP archive with clean, structured formatting.
  </Card>

  <Card title="Table Extraction" icon="table">
    Intelligent table detection and conversion to structured formats.
  </Card>

  <Card title="Batch Processing" icon="layer-group">
    Process multi-page documents and ZIP archives with automatic page handling.
  </Card>

  <Card title="Layout Preservation" icon="table-columns">
    Intelligent reading order detection and complex layout handling.
  </Card>

  <Card title="Enterprise-Ready" icon="building">
    Scalable API with job management, progress tracking, and error handling.
  </Card>
</CardGroup>

***

## Supported Languages

Document Intelligence supports all 22 Constitutionally recognized Indian languages:

<Tabs>
  <Tab title="Primary Languages">
    | Language  | Code    | Script     |
    | --------- | ------- | ---------- |
    | Hindi     | `hi-IN` | Devanagari |
    | Bengali   | `bn-IN` | Bengali    |
    | Tamil     | `ta-IN` | Tamil      |
    | Telugu    | `te-IN` | Telugu     |
    | Marathi   | `mr-IN` | Devanagari |
    | Gujarati  | `gu-IN` | Gujarati   |
    | Kannada   | `kn-IN` | Kannada    |
    | Malayalam | `ml-IN` | Malayalam  |
    | Odia      | `od-IN` | Odia       |
    | Punjabi   | `pa-IN` | Gurmukhi   |
    | English   | `en-IN` | Latin      |
  </Tab>

  <Tab title="Additional Languages">
    | Language | Code     | Script            |
    | -------- | -------- | ----------------- |
    | Assamese | `as-IN`  | Assamese          |
    | Urdu     | `ur-IN`  | Perso-Arabic      |
    | Sanskrit | `sa-IN`  | Devanagari        |
    | Nepali   | `ne-IN`  | Devanagari        |
    | Konkani  | `kok-IN` | Devanagari        |
    | Maithili | `mai-IN` | Devanagari        |
    | Sindhi   | `sd-IN`  | Devanagari/Arabic |
    | Kashmiri | `ks-IN`  | Perso-Arabic      |
    | Dogri    | `doi-IN` | Devanagari        |
    | Manipuri | `mni-IN` | Meetei Mayek      |
    | Bodo     | `brx-IN` | Devanagari        |
    | Santali  | `sat-IN` | Ol Chiki          |
  </Tab>
</Tabs>

***

## Supported Input Formats

| Format | Extension       | Description                                            |
| ------ | --------------- | ------------------------------------------------------ |
| PDF    | `.pdf`          | Multi-page PDF documents                               |
| PNG    | `.png`          | Document page images                                   |
| JPEG   | `.jpg`, `.jpeg` | Document page images                                   |
| ZIP    | `.zip`          | Flat archive containing document page images (JPG/PNG) |

<Note>
  For ZIP files, include only JPG and PNG document pages in a flat structure (no nested folders). The API will process all pages in the archive and maintain page order based on filename.
</Note>

***

## Quick Start

Get started with Document Intelligence in minutes:

<CodeGroup>
  <CodeBlock title="Python" active>
    ```python
    from sarvamai import SarvamAI

    client = SarvamAI(
        api_subscription_key="YOUR_SARVAM_API_KEY"
    )

    # Create a Document Intelligence job
    job = client.document_intelligence.create_job(
        language="hi-IN",           # Target language (BCP-47 format)
        output_format="md"          # Output format: "html" or "md" (delivered as ZIP)
    )

    # Upload your document
    job.upload_file("document.pdf")

    # Start processing
    job.start()

    # Wait for completion
    status = job.wait_until_complete()
    print(f"Job completed: {status.job_state}")

    # Get processing metrics
    metrics = job.get_page_metrics()
    print(f"Pages processed: {metrics['pages_processed']}")

    # Download the output (ZIP file containing the processed document)
    job.download_output("./output.zip")
    print("Output saved to ./output.zip")
    ```
  </CodeBlock>

  <CodeBlock title="JavaScript">
    ```javascript
    import { SarvamAIClient } from "sarvamai";

    const client = new SarvamAIClient({
        apiSubscriptionKey: "YOUR_SARVAM_API_KEY"
    });

    async function processDocument() {
        // Create a Document Intelligence job
        const job = await client.documentIntelligence.createJob({
            language: "hi-IN",
            outputFormat: "md"
        });

        // Upload your document
        await job.uploadFile("document.pdf");

        // Start processing
        await job.start();

        // Wait for completion
        const status = await job.waitUntilComplete();
        console.log(`Job completed: ${status.job_state}`);

        // Get processing metrics
        const metrics = job.getPageMetrics();
        console.log(`Pages processed: ${metrics.pagesProcessed}`);

        // Download the output (ZIP file containing the processed document)
        await job.downloadOutput("./output.zip");
        console.log("Output saved to ./output.zip");
    }

    processDocument();
    ```
  </CodeBlock>
</CodeGroup>

***

## Response Format

### Job Status Response

```json
{
  "job_id": "abc123-def456-ghi789",
  "job_state": "Completed",
  "created_at": "2026-02-04T10:30:00Z",
  "updated_at": "2026-02-04T10:35:00Z",
  "page_metrics": {
    "total_pages": 10,
    "pages_processed": 10,
    "pages_succeeded": 10,
    "pages_failed": 0
  }
}
```

### Job States

| State                | Description                         |
| -------------------- | ----------------------------------- |
| `Accepted`           | Job created, awaiting file upload   |
| `Pending`            | File uploaded, waiting to start     |
| `Running`            | Job is being processed              |
| `Completed`          | All pages processed successfully    |
| `PartiallyCompleted` | Some pages succeeded, some failed   |
| `Failed`             | All pages failed or job-level error |

***

## Error Handling

<Accordion title="Error Handling Example">
  ```python
  from sarvamai import SarvamAI
  from sarvamai.core.api_error import ApiError

  client = SarvamAI(api_subscription_key="YOUR_SARVAM_API_KEY")

  try:
      job = client.document_intelligence.create_job(
          language="hi-IN",
          output_format="md"
      )
      job.upload_file("document.pdf")
      job.start()
      status = job.wait_until_complete()
      
      if status.job_state == "Completed":
          job.download_output("./output.zip")
          print("Output saved to ./output.zip")
      else:
          print(f"Job failed: {status}")
          
  except ApiError as e:
      if e.status_code == 400:
          print(f"Bad request: {e.body}")
      elif e.status_code == 403:
          print("Invalid API key")
      elif e.status_code == 429:
          print("Rate limit exceeded")
      else:
          print(f"Error {e.status_code}: {e.body}")
  except FileNotFoundError:
      print("Document file not found")
  ```
</Accordion>

### Error Codes

| HTTP Status | Error Code                   | Description                                   |
| ----------- | ---------------------------- | --------------------------------------------- |
| `400`       | `invalid_request_error`      | Invalid parameters or missing required fields |
| `403`       | `invalid_api_key_error`      | Invalid or missing API key                    |
| `404`       | `not_found_error`            | Job not found                                 |
| `422`       | `unprocessable_entity_error` | Invalid file format or corrupted file         |
| `429`       | `insufficient_quota_error`   | Rate limit or quota exceeded                  |
| `500`       | `internal_server_error`      | Server error, retry the request               |

***

## Best Practices

<CardGroup cols={2}>
  <Card title="Choose the Right Format" icon="bullseye">
    Use Markdown for human-readable output and HTML for web rendering and rich formatting.
  </Card>

  <Card title="Specify Language" icon="language">
    Always specify the correct language code for optimal text extraction accuracy, especially for Indian languages.
  </Card>

  <Card title="Handle Large Documents" icon="file-pdf">
    For large documents, monitor `page_metrics` to track progress and handle partial failures gracefully.
  </Card>

  <Card title="Use HTML for Tables" icon="code">
    Choose HTML output format when you need to preserve table structures and rich formatting.
  </Card>
</CardGroup>

***

## Next Steps

<CardGroup cols={3}>
  <Card title="Sarvam Vision Model" icon="eye" href="/api-reference-docs/getting-started/models/sarvam-vision">
    Learn about the model powering Document Intelligence.
  </Card>

  <Card title="API Reference" icon="terminal" href="/api-reference-docs/document-intelligence">
    Complete API documentation with all parameters and options.
  </Card>

  <Card title="Try in API Dashboard" icon="play" href="https://dashboard.sarvam.ai">
    Upload and process documents in the API Dashboard.
  </Card>
</CardGroup>
```

# Create Document Intelligence Job

POST https://api.sarvam.ai/doc-digitization/job/v1
Content-Type: application/json

Creates a new Document Intelligence job.

**Supported Languages (BCP-47 format):**
- `hi-IN`: Hindi (default)
- `en-IN`: English
- `bn-IN`: Bengali
- `gu-IN`: Gujarati
- `kn-IN`: Kannada
- `ml-IN`: Malayalam
- `mr-IN`: Marathi
- `or-IN`: Odia
- `pa-IN`: Punjabi
- `ta-IN`: Tamil
- `te-IN`: Telugu
- `ur-IN`: Urdu
- `as-IN`: Assamese
- `bodo-IN`: Bodo
- `doi-IN`: Dogri
- `ks-IN`: Kashmiri
- `kok-IN`: Konkani
- `mai-IN`: Maithili
- `mni-IN`: Manipuri
- `ne-IN`: Nepali
- `sa-IN`: Sanskrit
- `sat-IN`: Santali
- `sd-IN`: Sindhi

**Output Formats (delivered as ZIP file):**
- `html`: Structured HTML files with layout preservation
- `md`: Markdown files (default)
- `json`: Structured JSON files for programmatic processing

Reference: https://docs.sarvam.ai/api-reference-docs/document-intelligence/initialise

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Create Document Intelligence Job
  version: endpoint_documentIntelligence.initialise
paths:
  /doc-digitization/job/v1:
    post:
      operationId: initialise
      summary: Create Document Intelligence Job
      description: |-
        Creates a new Document Intelligence job.

        **Supported Languages (BCP-47 format):**
        - `hi-IN`: Hindi (default)
        - `en-IN`: English
        - `bn-IN`: Bengali
        - `gu-IN`: Gujarati
        - `kn-IN`: Kannada
        - `ml-IN`: Malayalam
        - `mr-IN`: Marathi
        - `or-IN`: Odia
        - `pa-IN`: Punjabi
        - `ta-IN`: Tamil
        - `te-IN`: Telugu
        - `ur-IN`: Urdu
        - `as-IN`: Assamese
        - `bodo-IN`: Bodo
        - `doi-IN`: Dogri
        - `ks-IN`: Kashmiri
        - `kok-IN`: Konkani
        - `mai-IN`: Maithili
        - `mni-IN`: Manipuri
        - `ne-IN`: Nepali
        - `sa-IN`: Sanskrit
        - `sat-IN`: Santali
        - `sd-IN`: Sindhi

        **Output Formats (delivered as ZIP file):**
        - `html`: Structured HTML files with layout preservation
        - `md`: Markdown files (default)
        - `json`: Structured JSON files for programmatic processing
      tags:
        - - subpackage_documentIntelligence
      parameters:
        - name: api-subscription-key
          in: header
          required: true
          schema:
            type: string
      responses:
        '202':
          description: Successful Response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DocDigitizationCreateJobResponse'
        '400':
          description: Bad Request
          content: {}
        '403':
          description: Forbidden
          content: {}
        '429':
          description: Quota Exceeded / Rate Limited
          content: {}
        '500':
          description: Internal Server Error
          content: {}
        '503':
          description: Service Unavailable
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DocDigitizationCreateJobRequest'
components:
  schemas:
    DocDigitizationSupportedLanguage:
      type: string
      enum:
        - value: hi-IN
        - value: en-IN
        - value: bn-IN
        - value: gu-IN
        - value: kn-IN
        - value: ml-IN
        - value: mr-IN
        - value: or-IN
        - value: pa-IN
        - value: ta-IN
        - value: te-IN
        - value: ur-IN
        - value: as-IN
        - value: bodo-IN
        - value: doi-IN
        - value: ks-IN
        - value: kok-IN
        - value: mai-IN
        - value: mni-IN
        - value: ne-IN
        - value: sa-IN
        - value: sat-IN
        - value: sd-IN
    DocDigitizationOutputFormat:
      type: string
      enum:
        - value: html
        - value: md
        - value: json
    DocDigitizationJobParameters:
      type: object
      properties:
        language:
          $ref: '#/components/schemas/DocDigitizationSupportedLanguage'
          description: >-
            Primary language of the document in BCP-47 format. This helps
            optimize text extraction accuracy for the specified language.
        output_format:
          $ref: '#/components/schemas/DocDigitizationOutputFormat'
          description: >-
            Output format for the extracted content (delivered as a ZIP file).
            Use 'html' for structured HTML, 'md' for Markdown, or 'json' for
            structured JSON data.
    DocDigitizationWebhookCallback:
      type: object
      properties:
        url:
          type: string
          format: uri
          description: HTTPS webhook URL to call upon job completion (HTTP not allowed)
        auth_token:
          type: string
          default: ''
          description: Authorization token sent as X-SARVAM-JOB-CALLBACK-TOKEN header
      required:
        - url
    DocDigitizationCreateJobRequest:
      type: object
      properties:
        job_parameters:
          $ref: '#/components/schemas/DocDigitizationJobParameters'
          description: >-
            Configuration parameters for the Document Intelligence job including
            language and output format. Defaults to Hindi (hi-IN) and Markdown
            output if omitted.
        callback:
          oneOf:
            - $ref: '#/components/schemas/DocDigitizationWebhookCallback'
            - type: 'null'
          description: Optional webhook for completion notification
    StorageContainerType:
      type: string
      enum:
        - value: Azure
        - value: Local
        - value: Google
        - value: Azure_V1
    DocDigitizationJobState:
      type: string
      enum:
        - value: Accepted
        - value: Pending
        - value: Running
        - value: Completed
        - value: PartiallyCompleted
        - value: Failed
    DocDigitizationCreateJobResponse:
      type: object
      properties:
        job_id:
          type: string
          format: uuid
          description: Unique job identifier (UUID)
        storage_container_type:
          $ref: '#/components/schemas/StorageContainerType'
          description: Storage Container Type
        job_parameters:
          $ref: '#/components/schemas/DocDigitizationJobParameters'
          description: '  Job configuration parameters'
        job_state:
          $ref: '#/components/schemas/DocDigitizationJobState'
      required:
        - job_id
        - storage_container_type
        - job_parameters
        - job_state

```

## SDK Code Examples

```python
from sarvamai import SarvamAI

client = SarvamAI(
    api_subscription_key="YOUR_API_SUBSCRIPTION_KEY",
)
client.document_intelligence.initialise()

```

```typescript
import { SarvamAIClient } from "sarvamai";

const client = new SarvamAIClient({ apiSubscriptionKey: "YOUR_API_SUBSCRIPTION_KEY" });
await client.documentIntelligence.initialise();

```

```go
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.sarvam.ai/doc-digitization/job/v1"

	payload := strings.NewReader("{}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("api-subscription-key", "<apiKey>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.sarvam.ai/doc-digitization/job/v1")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["api-subscription-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.sarvam.ai/doc-digitization/job/v1")
  .header("api-subscription-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.sarvam.ai/doc-digitization/job/v1', [
  'body' => '{}',
  'headers' => [
    'Content-Type' => 'application/json',
    'api-subscription-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.sarvam.ai/doc-digitization/job/v1");
var request = new RestRequest(Method.POST);
request.AddHeader("api-subscription-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "api-subscription-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = [] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.sarvam.ai/doc-digitization/job/v1")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Get Document Intelligence Upload URLs

POST https://api.sarvam.ai/doc-digitization/job/v1/upload-files
Content-Type: application/json

Returns presigned URLs for uploading input files.

**File Constraints:**
- Exactly one file required (PDF or ZIP)
- PDF files: `.pdf` extension
- ZIP files: `.zip` extension

Reference: https://docs.sarvam.ai/api-reference-docs/document-intelligence/get-upload-links

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get Document Intelligence Upload URLs
  version: endpoint_documentIntelligence.get_upload_links
paths:
  /doc-digitization/job/v1/upload-files:
    post:
      operationId: get-upload-links
      summary: Get Document Intelligence Upload URLs
      description: |-
        Returns presigned URLs for uploading input files.

        **File Constraints:**
        - Exactly one file required (PDF or ZIP)
        - PDF files: `.pdf` extension
        - ZIP files: `.zip` extension
      tags:
        - - subpackage_documentIntelligence
      parameters:
        - name: api-subscription-key
          in: header
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DocDigitizationUploadFilesResponse'
        '400':
          description: Bad Request
          content: {}
        '403':
          description: Forbidden
          content: {}
        '429':
          description: Quota Exceeded / Rate Limited
          content: {}
        '500':
          description: Internal Server Error
          content: {}
        '503':
          description: Service Unavailable
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DocDigitizationUploadFilesRequest'
components:
  schemas:
    DocDigitizationUploadFilesRequest:
      type: object
      properties:
        job_id:
          type: string
          description: Job identifier returned from Create Job
        files:
          type: array
          items:
            type: string
          description: 'List of filenames to upload (exactly 1 file: PDF or ZIP)'
      required:
        - job_id
        - files
    DocDigitizationJobState:
      type: string
      enum:
        - value: Accepted
        - value: Pending
        - value: Running
        - value: Completed
        - value: PartiallyCompleted
        - value: Failed
    FileSignedURLDetails:
      type: object
      properties:
        file_url:
          type: string
        file_metadata:
          type:
            - object
            - 'null'
          additionalProperties:
            description: Any type
      required:
        - file_url
    StorageContainerType:
      type: string
      enum:
        - value: Azure
        - value: Local
        - value: Google
        - value: Azure_V1
    DocDigitizationUploadFilesResponse:
      type: object
      properties:
        job_id:
          type: string
          format: uuid
          description: Job identifier
        job_state:
          $ref: '#/components/schemas/DocDigitizationJobState'
          description: Current job state
        upload_urls:
          type: object
          additionalProperties:
            $ref: '#/components/schemas/FileSignedURLDetails'
          description: Map of filename to presigned upload URL details
        storage_container_type:
          $ref: '#/components/schemas/StorageContainerType'
          description: Storage backend type
      required:
        - job_id
        - job_state
        - upload_urls
        - storage_container_type

```

## SDK Code Examples

```python
from sarvamai import SarvamAI

client = SarvamAI(
    api_subscription_key="YOUR_API_SUBSCRIPTION_KEY",
)
client.document_intelligence.get_upload_links(
    job_id="job_id",
    files=["files"],
)

```

```typescript
import { SarvamAIClient } from "sarvamai";

const client = new SarvamAIClient({ apiSubscriptionKey: "YOUR_API_SUBSCRIPTION_KEY" });
await client.documentIntelligence.getUploadLinks({
    job_id: "job_id",
    files: ["files"]
});

```

```go
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.sarvam.ai/doc-digitization/job/v1/upload-files"

	payload := strings.NewReader("{\n  \"job_id\": \"string\",\n  \"files\": [\n    \"string\"\n  ]\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("api-subscription-key", "<apiKey>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.sarvam.ai/doc-digitization/job/v1/upload-files")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["api-subscription-key"] = '<apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"job_id\": \"string\",\n  \"files\": [\n    \"string\"\n  ]\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.sarvam.ai/doc-digitization/job/v1/upload-files")
  .header("api-subscription-key", "<apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"job_id\": \"string\",\n  \"files\": [\n    \"string\"\n  ]\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.sarvam.ai/doc-digitization/job/v1/upload-files', [
  'body' => '{
  "job_id": "string",
  "files": [
    "string"
  ]
}',
  'headers' => [
    'Content-Type' => 'application/json',
    'api-subscription-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.sarvam.ai/doc-digitization/job/v1/upload-files");
var request = new RestRequest(Method.POST);
request.AddHeader("api-subscription-key", "<apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"job_id\": \"string\",\n  \"files\": [\n    \"string\"\n  ]\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "api-subscription-key": "<apiKey>",
  "Content-Type": "application/json"
]
let parameters = [
  "job_id": "string",
  "files": ["string"]
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.sarvam.ai/doc-digitization/job/v1/upload-files")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Start Document Intelligence Job

POST https://api.sarvam.ai/doc-digitization/job/v1/{job_id}/start

Validates the uploaded file and starts processing.

**Validation Checks:**
- File must be uploaded before starting
- File size must not exceed 200 MB
- PDF must be parseable by the PDF parser
- ZIP must contain only JPEG/PNG images
- ZIP must be flat (no nested folders beyond one level)
- ZIP must contain at least one valid image
- Page/image count must not exceed 500
- User must have sufficient credits

**Processing:**
Job runs asynchronously. Poll the status endpoint or use webhook callback for completion notification.

Reference: https://docs.sarvam.ai/api-reference-docs/document-intelligence/start

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Start Document Intelligence Job
  version: endpoint_documentIntelligence.start
paths:
  /doc-digitization/job/v1/{job_id}/start:
    post:
      operationId: start
      summary: Start Document Intelligence Job
      description: >-
        Validates the uploaded file and starts processing.


        **Validation Checks:**

        - File must be uploaded before starting

        - File size must not exceed 200 MB

        - PDF must be parseable by the PDF parser

        - ZIP must contain only JPEG/PNG images

        - ZIP must be flat (no nested folders beyond one level)

        - ZIP must contain at least one valid image

        - Page/image count must not exceed 500

        - User must have sufficient credits


        **Processing:**

        Job runs asynchronously. Poll the status endpoint or use webhook
        callback for completion notification.
      tags:
        - - subpackage_documentIntelligence
      parameters:
        - name: job_id
          in: path
          description: The unique identifier of the job
          required: true
          schema:
            type: string
            format: uuid
        - name: api-subscription-key
          in: header
          required: true
          schema:
            type: string
      responses:
        '202':
          description: Successful Response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DocDigitizationJobStatusResponse'
        '400':
          description: Bad Request
          content: {}
        '403':
          description: Forbidden
          content: {}
        '429':
          description: Quota Exceeded / Rate Limited
          content: {}
        '500':
          description: Internal Server Error
          content: {}
        '503':
          description: Service Unavailable
          content: {}
components:
  schemas:
    DocDigitizationJobState:
      type: string
      enum:
        - value: Accepted
        - value: Pending
        - value: Running
        - value: Completed
        - value: PartiallyCompleted
        - value: Failed
    StorageContainerType:
      type: string
      enum:
        - value: Azure
        - value: Local
        - value: Google
        - value: Azure_V1
    TaskFileDetails:
      type: object
      properties:
        file_name:
          type: string
        file_id:
          type: string
      required:
        - file_name
        - file_id
    DocDigitizationJobDetailState:
      type: string
      enum:
        - value: Pending
        - value: Running
        - value: Success
        - value: PartialSuccess
        - value: Failed
    DocDigitizationPageError:
      type: object
      properties:
        page_number:
          type: integer
          description: Page number that failed
        error_code:
          type: string
          description: Standardized error code
        error_message:
          type: string
          description: Human-readable error description
      required:
        - page_number
        - error_code
        - error_message
    DocDigitizationJobDetail:
      type: object
      properties:
        inputs:
          type: array
          items:
            $ref: '#/components/schemas/TaskFileDetails'
          description: Input file(s) for this task
        outputs:
          type: array
          items:
            $ref: '#/components/schemas/TaskFileDetails'
          description: Output file(s) produced
        state:
          $ref: '#/components/schemas/DocDigitizationJobDetailState'
          description: Processing state for this file
        total_pages:
          type: integer
          default: 0
          description: Total pages/images in the input file
        pages_processed:
          type: integer
          default: 0
          description: Number of pages processed so far
        pages_succeeded:
          type: integer
          default: 0
          description: Number of pages successfully processed
        pages_failed:
          type: integer
          default: 0
          description: Number of pages that failed processing
        error_message:
          type: string
          default: ''
          description: Error message if processing failed
        error_code:
          type:
            - string
            - 'null'
          description: Standardized error code if failed
        page_errors:
          type: array
          items:
            $ref: '#/components/schemas/DocDigitizationPageError'
          description: Detailed errors for each failed page
      required:
        - inputs
        - outputs
        - state
    DocDigitizationJobStatusResponse:
      type: object
      properties:
        job_id:
          type: string
          format: uuid
          description: Job identifier (UUID)
        job_state:
          $ref: '#/components/schemas/DocDigitizationJobState'
          description: Current job state
        created_at:
          type: string
          format: date-time
          description: Job creation timestamp (ISO 8601)
        updated_at:
          type: string
          format: date-time
          description: Last update timestamp (ISO 8601)
        storage_container_type:
          $ref: '#/components/schemas/StorageContainerType'
          description: Storage backend type
        total_files:
          type: integer
          default: 0
          description: Total input files (always 1)
        successful_files_count:
          type: integer
          default: 0
          description: Files that completed successfully
        failed_files_count:
          type: integer
          default: 0
          description: Files that failed
        error_message:
          type: string
          default: ''
          description: Job-level error message
        job_details:
          type: array
          items:
            $ref: '#/components/schemas/DocDigitizationJobDetail'
          description: Per-file processing details with page metrics
      required:
        - job_id
        - job_state
        - created_at
        - updated_at
        - storage_container_type

```

## SDK Code Examples

```python
from sarvamai import SarvamAI

client = SarvamAI(
    api_subscription_key="YOUR_API_SUBSCRIPTION_KEY",
)
client.document_intelligence.start(
    job_id="job_id",
)

```

```typescript
import { SarvamAIClient } from "sarvamai";

const client = new SarvamAIClient({ apiSubscriptionKey: "YOUR_API_SUBSCRIPTION_KEY" });
await client.documentIntelligence.start("job_id");

```

```go
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.sarvam.ai/doc-digitization/job/v1/job_id/start"

	req, _ := http.NewRequest("POST", url, nil)

	req.Header.Add("api-subscription-key", "<apiKey>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.sarvam.ai/doc-digitization/job/v1/job_id/start")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["api-subscription-key"] = '<apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.sarvam.ai/doc-digitization/job/v1/job_id/start")
  .header("api-subscription-key", "<apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.sarvam.ai/doc-digitization/job/v1/job_id/start', [
  'headers' => [
    'api-subscription-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.sarvam.ai/doc-digitization/job/v1/job_id/start");
var request = new RestRequest(Method.POST);
request.AddHeader("api-subscription-key", "<apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["api-subscription-key": "<apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.sarvam.ai/doc-digitization/job/v1/job_id/start")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Get Document Intelligence Job Status

GET https://api.sarvam.ai/doc-digitization/job/v1/{job_id}/status

Returns the current status of a job with page-level metrics.

**Job States:**
- `Accepted`: Job created, awaiting file upload
- `Pending`: File uploaded, waiting to start
- `Running`: Processing in progress
- `Completed`: All pages processed successfully
- `PartiallyCompleted`: Some pages succeeded, some failed
- `Failed`: All pages failed or job-level error

**Page Metrics:**
Response includes detailed progress: total pages, pages processed, succeeded, failed, and per-page errors.

Reference: https://docs.sarvam.ai/api-reference-docs/document-intelligence/get-status

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get Document Intelligence Job Status
  version: endpoint_documentIntelligence.get_status
paths:
  /doc-digitization/job/v1/{job_id}/status:
    get:
      operationId: get-status
      summary: Get Document Intelligence Job Status
      description: >-
        Returns the current status of a job with page-level metrics.


        **Job States:**

        - `Accepted`: Job created, awaiting file upload

        - `Pending`: File uploaded, waiting to start

        - `Running`: Processing in progress

        - `Completed`: All pages processed successfully

        - `PartiallyCompleted`: Some pages succeeded, some failed

        - `Failed`: All pages failed or job-level error


        **Page Metrics:**

        Response includes detailed progress: total pages, pages processed,
        succeeded, failed, and per-page errors.
      tags:
        - - subpackage_documentIntelligence
      parameters:
        - name: job_id
          in: path
          description: The unique identifier of the job
          required: true
          schema:
            type: string
            format: uuid
        - name: api-subscription-key
          in: header
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DocDigitizationJobStatusResponse'
        '400':
          description: Bad Request
          content: {}
        '403':
          description: Forbidden
          content: {}
        '429':
          description: Quota Exceeded / Rate Limited
          content: {}
        '500':
          description: Internal Server Error
          content: {}
        '503':
          description: Service Unavailable
          content: {}
components:
  schemas:
    DocDigitizationJobState:
      type: string
      enum:
        - value: Accepted
        - value: Pending
        - value: Running
        - value: Completed
        - value: PartiallyCompleted
        - value: Failed
    StorageContainerType:
      type: string
      enum:
        - value: Azure
        - value: Local
        - value: Google
        - value: Azure_V1
    TaskFileDetails:
      type: object
      properties:
        file_name:
          type: string
        file_id:
          type: string
      required:
        - file_name
        - file_id
    DocDigitizationJobDetailState:
      type: string
      enum:
        - value: Pending
        - value: Running
        - value: Success
        - value: PartialSuccess
        - value: Failed
    DocDigitizationPageError:
      type: object
      properties:
        page_number:
          type: integer
          description: Page number that failed
        error_code:
          type: string
          description: Standardized error code
        error_message:
          type: string
          description: Human-readable error description
      required:
        - page_number
        - error_code
        - error_message
    DocDigitizationJobDetail:
      type: object
      properties:
        inputs:
          type: array
          items:
            $ref: '#/components/schemas/TaskFileDetails'
          description: Input file(s) for this task
        outputs:
          type: array
          items:
            $ref: '#/components/schemas/TaskFileDetails'
          description: Output file(s) produced
        state:
          $ref: '#/components/schemas/DocDigitizationJobDetailState'
          description: Processing state for this file
        total_pages:
          type: integer
          default: 0
          description: Total pages/images in the input file
        pages_processed:
          type: integer
          default: 0
          description: Number of pages processed so far
        pages_succeeded:
          type: integer
          default: 0
          description: Number of pages successfully processed
        pages_failed:
          type: integer
          default: 0
          description: Number of pages that failed processing
        error_message:
          type: string
          default: ''
          description: Error message if processing failed
        error_code:
          type:
            - string
            - 'null'
          description: Standardized error code if failed
        page_errors:
          type: array
          items:
            $ref: '#/components/schemas/DocDigitizationPageError'
          description: Detailed errors for each failed page
      required:
        - inputs
        - outputs
        - state
    DocDigitizationJobStatusResponse:
      type: object
      properties:
        job_id:
          type: string
          format: uuid
          description: Job identifier (UUID)
        job_state:
          $ref: '#/components/schemas/DocDigitizationJobState'
          description: Current job state
        created_at:
          type: string
          format: date-time
          description: Job creation timestamp (ISO 8601)
        updated_at:
          type: string
          format: date-time
          description: Last update timestamp (ISO 8601)
        storage_container_type:
          $ref: '#/components/schemas/StorageContainerType'
          description: Storage backend type
        total_files:
          type: integer
          default: 0
          description: Total input files (always 1)
        successful_files_count:
          type: integer
          default: 0
          description: Files that completed successfully
        failed_files_count:
          type: integer
          default: 0
          description: Files that failed
        error_message:
          type: string
          default: ''
          description: Job-level error message
        job_details:
          type: array
          items:
            $ref: '#/components/schemas/DocDigitizationJobDetail'
          description: Per-file processing details with page metrics
      required:
        - job_id
        - job_state
        - created_at
        - updated_at
        - storage_container_type

```

## SDK Code Examples

```python
from sarvamai import SarvamAI

client = SarvamAI(
    api_subscription_key="YOUR_API_SUBSCRIPTION_KEY",
)
client.document_intelligence.get_status(
    job_id="job_id",
)

```

```typescript
import { SarvamAIClient } from "sarvamai";

const client = new SarvamAIClient({ apiSubscriptionKey: "YOUR_API_SUBSCRIPTION_KEY" });
await client.documentIntelligence.getStatus("job_id");

```

```go
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.sarvam.ai/doc-digitization/job/v1/job_id/status"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("api-subscription-key", "<apiKey>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.sarvam.ai/doc-digitization/job/v1/job_id/status")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["api-subscription-key"] = '<apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.sarvam.ai/doc-digitization/job/v1/job_id/status")
  .header("api-subscription-key", "<apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.sarvam.ai/doc-digitization/job/v1/job_id/status', [
  'headers' => [
    'api-subscription-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.sarvam.ai/doc-digitization/job/v1/job_id/status");
var request = new RestRequest(Method.GET);
request.AddHeader("api-subscription-key", "<apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["api-subscription-key": "<apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.sarvam.ai/doc-digitization/job/v1/job_id/status")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Get Document Intelligence Download URLs

POST https://api.sarvam.ai/doc-digitization/job/v1/{job_id}/download-files

Returns presigned URLs for downloading output files.

**Prerequisites:**
- Job must be in `Completed` or `PartiallyCompleted` state
- Failed jobs have no output available

Reference: https://docs.sarvam.ai/api-reference-docs/document-intelligence/get-download-links

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get Document Intelligence Download URLs
  version: endpoint_documentIntelligence.get_download_links
paths:
  /doc-digitization/job/v1/{job_id}/download-files:
    post:
      operationId: get-download-links
      summary: Get Document Intelligence Download URLs
      description: |-
        Returns presigned URLs for downloading output files.

        **Prerequisites:**
        - Job must be in `Completed` or `PartiallyCompleted` state
        - Failed jobs have no output available
      tags:
        - - subpackage_documentIntelligence
      parameters:
        - name: job_id
          in: path
          description: The unique identifier of the job
          required: true
          schema:
            type: string
            format: uuid
        - name: api-subscription-key
          in: header
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DocDigitizationDownloadFilesResponse'
        '400':
          description: Bad Request
          content: {}
        '403':
          description: Forbidden
          content: {}
        '429':
          description: Quota Exceeded / Rate Limited
          content: {}
        '500':
          description: Internal Server Error
          content: {}
        '503':
          description: Service Unavailable
          content: {}
components:
  schemas:
    DocDigitizationJobState:
      type: string
      enum:
        - value: Accepted
        - value: Pending
        - value: Running
        - value: Completed
        - value: PartiallyCompleted
        - value: Failed
    StorageContainerType:
      type: string
      enum:
        - value: Azure
        - value: Local
        - value: Google
        - value: Azure_V1
    FileSignedURLDetails:
      type: object
      properties:
        file_url:
          type: string
        file_metadata:
          type:
            - object
            - 'null'
          additionalProperties:
            description: Any type
      required:
        - file_url
    DocDigitizationDownloadFilesResponse:
      type: object
      properties:
        job_id:
          type: string
          format: uuid
          description: Job identifier (UUID)
        job_state:
          $ref: '#/components/schemas/DocDigitizationJobState'
          description: Current job state
        storage_container_type:
          $ref: '#/components/schemas/StorageContainerType'
          description: Storage backend type
        download_urls:
          type: object
          additionalProperties:
            $ref: '#/components/schemas/FileSignedURLDetails'
          description: Map of filename to presigned download URL details
        error_code:
          type:
            - string
            - 'null'
        error_message:
          type:
            - string
            - 'null'
      required:
        - job_id
        - job_state
        - storage_container_type
        - download_urls

```

## SDK Code Examples

```python
from sarvamai import SarvamAI

client = SarvamAI(
    api_subscription_key="YOUR_API_SUBSCRIPTION_KEY",
)
client.document_intelligence.get_download_links(
    job_id="job_id",
)

```

```typescript
import { SarvamAIClient } from "sarvamai";

const client = new SarvamAIClient({ apiSubscriptionKey: "YOUR_API_SUBSCRIPTION_KEY" });
await client.documentIntelligence.getDownloadLinks("job_id");

```

```go
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.sarvam.ai/doc-digitization/job/v1/job_id/download-files"

	req, _ := http.NewRequest("POST", url, nil)

	req.Header.Add("api-subscription-key", "<apiKey>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.sarvam.ai/doc-digitization/job/v1/job_id/download-files")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["api-subscription-key"] = '<apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.sarvam.ai/doc-digitization/job/v1/job_id/download-files")
  .header("api-subscription-key", "<apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.sarvam.ai/doc-digitization/job/v1/job_id/download-files', [
  'headers' => [
    'api-subscription-key' => '<apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.sarvam.ai/doc-digitization/job/v1/job_id/download-files");
var request = new RestRequest(Method.POST);
request.AddHeader("api-subscription-key", "<apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["api-subscription-key": "<apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.sarvam.ai/doc-digitization/job/v1/job_id/download-files")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```