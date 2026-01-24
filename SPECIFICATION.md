# YT_BOT - Functional Specification

## Project Overview

**YT_BOT** is an automated YouTube Shorts generation and upload system. It leverages local AI models (Ollama for scripts), text-to-speech (Piper TTS), speech-to-text (Whisper), and video processing (FFmpeg) to create engaging short-form content autonomously.

**Current Implementation Status:**
- ✅ AI Script Generation (Ollama with multiple model support)
- ✅ Text-to-Speech Audio Generation (Piper TTS)  
- ✅ Subtitle Generation (Whisper)
- ✅ Video Rendering with styled subtitles (FFmpeg)
- ✅ YouTube Upload (OAuth 2.0)
- ✅ SEO-optimized titles and hashtag-rich descriptions

**Planned Enhancements:**
- 🔄 Batch Processing (multiple videos from topic list)
- 🔄 Scheduling (automated daily uploads)
- 🔄 AI Video Selection (Pexels/Pixabay API integration)
- 🔄 Background Music Integration
- 🔄 AI Model Rotation for content variety

**Goal:** Fully autonomous YouTube Shorts creation with minimal human intervention.

---

## Table of Contents

1. [Core Functional Requirements](#core-functional-requirements)
2. [System Architecture](#system-architecture)
3. [Required Capabilities](#required-capabilities)
4. [Data Models](#data-models)
5. [Processing Workflows](#processing-workflows)
6. [Configuration Requirements](#configuration-requirements)
7. [Error Handling Requirements](#error-handling-requirements)
8. [Content Safety Requirements](#content-safety-requirements)
9. [Deployment Requirements](#deployment-requirements)
10. [Implementation Freedom](#implementation-freedom)

---

## Current Implementation Features

### IF-1: Script Generation Engine

| ID | Feature | Status |
|----|---------|--------|
| IF-1.1 | Generate informative scripts with Ollama (multiple models) | ✅ Implemented |
| IF-1.2 | Create SEO-optimized titles (max 60 chars) | ✅ Implemented |
| IF-1.3 | Generate hashtag-rich descriptions | ✅ Implemented |
| IF-1.4 | Include natural CTAs (like, subscribe, share) | ✅ Implemented |
| IF-1.5 | 30-60 second script duration | ✅ Implemented |

### IF-2: Audio & Subtitle Generation

| ID | Feature | Status |
|----|---------|--------|
| IF-2.1 | Text-to-speech with Piper TTS (local) | ✅ Implemented |
| IF-2.2 | Subtitle generation with Whisper | ✅ Implemented |
| IF-2.3 | Styled subtitles (top-positioned, outlined) | ✅ Implemented |

### IF-3: Video Rendering

| ID | Feature | Status  |
|----|---------|---------|
| IF-3.1 | Vertical 9:16 video format | ✅ Implemented |
| IF-3.2 | Stock video backgrounds | ✅ Implemented |
| IF-3.3 | Subtitle burning with custom styling | ✅ Implemented |
| IF-3.4 | Smart background music mixing | 🔄 Planned |
| IF-3.5 | AI-based video selection (Pexels/Pixabay) | 🔄 Planned |

### IF-4: YouTube Integration

| ID | Feature | Status |
|----|---------|--------|
| IF-4.1 | OAuth 2.0 authentication | ✅ Implemented |
| IF-4.2 | Video upload with metadata | ✅ Implemented |
| IF-4.3 | Configurable privacy settings | ✅ Implemented |

### IF-5: Automation Features (Planned)

| ID | Feature | Status |
|----|---------|--------|
| IF-5.1 | Batch processing from topic list | 🔄 Planned |
| IF-5.2 | Scheduled daily uploads | 🔄 Planned |
| IF-5.3 | AI model rotation | 🔄 Planned |
| IF-5.4 | Error handling and retry logic | 🔄 Planned |

---

## Core Functional Requirements

### FR-1: Topic Management

| ID | Requirement |
|----|-------------|
| FR-1.1 | System shall maintain a queue of video topics to process |
| FR-1.2 | System shall support two input modes: simple topics (one-liners) and full scripts |
| FR-1.3 | System shall track completed topics separately from pending topics |
| FR-1.4 | System shall support trend-based topic generation (e.g., "AI trends : 3" generates 3 AI topics) |
| FR-1.5 | System shall auto-generate new topics when queue is empty (configurable) |
| FR-1.6 | Topics shall be removed from queue only after successful completion |

### FR-2: Video Generation

| ID | Requirement |
|----|-------------|
| FR-2.1 | System shall generate videos from text topics/scripts |
| FR-2.2 | System shall support configurable video lengths (short ~1min, long ~10min) |
| FR-2.3 | System shall handle video generation service authentication automatically |
| FR-2.4 | System shall wait for video generation to complete (may take 10-30+ minutes) |
| FR-2.5 | System shall download generated videos to local storage |
| FR-2.6 | System shall extract video metadata (title, description, outline/timestamps) |

### FR-3: YouTube Publishing

| ID | Requirement |
|----|-------------|
| FR-3.1 | System shall upload videos to YouTube with metadata |
| FR-3.2 | System shall support configurable privacy status (private/unlisted/public) |
| FR-3.3 | System shall handle YouTube API authentication via OAuth |
| FR-3.4 | System shall track upload quota and stop when exceeded |
| FR-3.5 | System shall save YouTube video URL after successful upload |
| FR-3.6 | System shall retry failed uploads on next run |

### FR-4: AI Enhancement (Optional)

| ID | Requirement |
|----|-------------|
| FR-4.1 | System may enhance topics before video generation for better content |
| FR-4.2 | System may enhance metadata (title, description, tags) for SEO |
| FR-4.3 | System may auto-generate topics using AI when queue is empty |
| FR-4.4 | AI enhancement shall be optional and configurable |

### FR-5: Parallel Processing

| ID | Requirement |
|----|-------------|
| FR-5.1 | System shall process multiple videos concurrently |
| FR-5.2 | Concurrency level shall be configurable (e.g., 1-8 workers) |
| FR-5.3 | Each worker shall operate independently |
| FR-5.4 | Failed workers shall not affect other workers |

### FR-6: Continuous Operation

| ID | Requirement |
|----|-------------|
| FR-6.1 | System shall run continuously until stopped |
| FR-6.2 | System shall wait 24 hours when YouTube quota is exhausted, then resume |
| FR-6.3 | System shall generate new topics when queue is empty (if enabled) |
| FR-6.4 | System shall retry failed topics up to N times (configurable) |

---

## System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR                                 │
│  Manages workflow, parallel workers, retries, and continuous loop   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐        │
│  │ Topic Manager  │  │ Content Filter │  │  AI Enhancer   │        │
│  │                │  │                │  │   (optional)   │        │
│  └────────────────┘  └────────────────┘  └────────────────┘        │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                       WORKER POOL                                    │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                   │
│  │Worker 1 │ │Worker 2 │ │Worker 3 │ │Worker N │  (configurable)   │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘                   │
├─────────────────────────────────────────────────────────────────────┤
│                    PER-WORKER PIPELINE                               │
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │  Temporary   │ →  │    Video     │ →  │   YouTube    │          │
│  │   Account    │    │  Generation  │    │   Uploader   │          │
│  │   Handler    │    │   Handler    │    │              │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │  Temporary  │    │    Video    │    │  YouTube    │
   │   Email     │    │ Generation  │    │    API      │
   │   Service   │    │   Service   │    │             │
   └─────────────┘    └─────────────┘    └─────────────┘
```

### Data Flow

```
                    ┌─────────────────┐
                    │  Topic Sources  │
                    ├─────────────────┤
                    │ • Topic file    │
                    │ • Script files  │
                    │ • Trends file   │
                    │ • AI generation │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Content Filter  │
                    │ (block unsafe)  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Topic Queue    │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │ Worker 1 │   │ Worker 2 │   │ Worker N │
        └────┬─────┘   └────┬─────┘   └────┬─────┘
             │              │              │
             ▼              ▼              ▼
        ┌─────────────────────────────────────────┐
        │           Per-Worker Pipeline            │
        ├─────────────────────────────────────────┤
        │ 1. Create temp account (email verify)   │
        │ 2. Submit video prompt                   │
        │ 3. Wait for generation                   │
        │ 4. Download video                        │
        │ 5. Extract metadata                      │
        │ 6. (Optional) AI enhance metadata       │
        │ 7. Upload to YouTube                     │
        │ 8. Mark topic completed                  │
        └─────────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    Outputs      │
                    ├─────────────────┤
                    │ • Video files   │
                    │ • Metadata      │
                    │ • YouTube URLs  │
                    │ • Completed log │
                    └─────────────────┘
```

---

## Required Capabilities

### Capability 1: Temporary Email Service

**Purpose:** Create disposable email addresses for video service account registration

**Required Functions:**
| Function | Input | Output |
|----------|-------|--------|
| `createEmail()` | None | Email address + session token |
| `checkInbox(token)` | Session token | List of emails |
| `getEmailBody(token, emailId)` | Token, email ID | Email content |

**Implementation Options:**
- Guerrilla Mail API
- Temp-Mail API
- Mailinator API
- 10MinuteMail
- Self-hosted mail server
- Any disposable email service with API

### Capability 2: Video Generation Service

**Purpose:** Convert text topics/scripts into video content

**Required Functions:**
| Function | Input | Output |
|----------|-------|--------|
| `authenticate(email, code)` | Email, verification code | Session |
| `submitPrompt(session, prompt)` | Session, video prompt | Job ID |
| `checkProgress(session, jobId)` | Session, job ID | Progress % |
| `downloadVideo(session, jobId)` | Session, job ID | Video file |
| `getMetadata(session, jobId)` | Session, job ID | Title, description, outline |

**Implementation Options:**
- InVideo AI
- Pictory AI
- Synthesia
- Runway ML
- Lumen5
- Kapwing
- Any AI video generation platform

**Considerations:**
- Some services require paid plans
- Some have API access, others need browser automation
- Generation time varies (5-30+ minutes)
- Quality and style vary significantly

### Capability 3: YouTube Upload Service

**Purpose:** Publish videos to YouTube with metadata

**Required Functions:**
| Function | Input | Output |
|----------|-------|--------|
| `authenticate()` | OAuth flow | Access token |
| `uploadVideo(token, video, metadata)` | Token, file, metadata | Video ID, URL |
| `checkQuota(token)` | Token | Remaining quota |

**Implementation Options:**
- YouTube Data API v3 (official)
- No alternatives (YouTube is the target)

**Quota Considerations:**
- Default: 10,000 units/day
- Upload: ~1,600 units each
- Approximately 6 uploads/day on default quota

### Capability 4: AI Text Generation (Optional)

**Purpose:** Enhance content and generate topics

**Required Functions:**
| Function | Input | Output |
|----------|-------|--------|
| `generateText(prompt)` | Text prompt | Generated text |

**Use Cases:**
- Enhance topics before video generation
- Generate SEO-optimized titles/descriptions/tags
- Auto-generate new topics when queue empty

**Implementation Options:**
- OpenAI API (GPT-4, GPT-3.5)
- Anthropic API (Claude)
- Google AI (Gemini)
- Local models (Ollama, LM Studio, vLLM)
- Cohere
- Mistral AI
- Any LLM with text generation capability

### Capability 5: Trending Topics Service (Optional)

**Purpose:** Fetch current trending topics for content ideas

**Required Functions:**
| Function | Input | Output |
|----------|-------|--------|
| `searchTrending(category)` | Category/query | List of topics |

**Implementation Options:**
- Tavily API
- Google Trends API
- NewsAPI
- Bing News Search
- Twitter/X Trends API
- Reddit API
- Custom web scraping

---

## Data Models

### Topic

```typescript
interface Topic {
  content: string;        // The topic text or script
  type: 'topic' | 'script';
  source: 'file' | 'trends' | 'ai_generated';
  status: 'pending' | 'processing' | 'completed' | 'failed';
  retryCount: number;
  createdAt: Date;
}
```

### Video

```typescript
interface Video {
  topicId: string;
  filePath: string;
  title: string;
  description: string;
  outline: string[];      // Timestamps/sections
  duration: number;       // seconds
  generatedAt: Date;
}
```

### VideoMetadata

```typescript
interface VideoMetadata {
  originalTitle: string;
  originalDescription: string;
  enhancedTitle?: string;
  enhancedDescription?: string;
  tags: string[];
  category: string;
}
```

### YouTubeUpload

```typescript
interface YouTubeUpload {
  videoId: string;
  watchUrl: string;
  studioUrl: string;
  privacyStatus: 'private' | 'unlisted' | 'public';
  uploadedAt: Date;
}
```

### WorkerResult

```typescript
interface WorkerResult {
  success: boolean;
  topic: string;
  video?: Video;
  upload?: YouTubeUpload;
  error?: string;
  attempt: number;
}
```

---

## Processing Workflows

### Main Workflow

```
START
  │
  ├─→ Load configuration
  │
  ├─→ Initialize services (email, video, youtube, ai)
  │
  ├─→ CONTINUOUS LOOP:
  │     │
  │     ├─→ Retry Phase
  │     │     • Upload orphaned videos (downloaded but not uploaded)
  │     │     • Reprocess failed topics
  │     │
  │     ├─→ Trends Phase
  │     │     • Parse trends file ("Topic : count" format)
  │     │     • Generate topics for each trend
  │     │     • Add to front of queue (priority)
  │     │
  │     ├─→ Auto-Generate Phase (if queue empty & enabled)
  │     │     • Use AI to generate N new topics
  │     │     • Filter through content safety
  │     │     • Add to queue
  │     │
  │     ├─→ Processing Phase
  │     │     • Create worker pool (configurable size)
  │     │     • Process topics in parallel
  │     │     • Track successes and failures
  │     │     • Retry failed topics up to maxRetries
  │     │
  │     ├─→ If YouTube quota exceeded:
  │     │     • Wait 24 hours
  │     │     • Reset quota tracking
  │     │     • Continue loop
  │     │
  │     └─→ If autoGenerate enabled:
  │           • Wait brief delay
  │           • Continue loop (generate more topics)
  │
  └─→ END (if autoGenerate disabled and queue empty)
```

### Per-Worker Video Pipeline

```
WORKER START (with topic)
  │
  ├─→ AI enhance topic (optional)
  │     • Send to AI for refinement
  │     • Validate through content filter
  │
  ├─→ Create temporary account
  │     │
  │     ├─→ Get temp email address
  │     ├─→ Start signup on video service
  │     ├─→ Wait for verification email (timeout: 5 min)
  │     ├─→ Extract verification code
  │     └─→ Complete signup with code
  │
  ├─→ Submit video prompt
  │     • Use configured prompt template
  │     • Insert topic into template
  │
  ├─→ Wait for generation
  │     │
  │     ├─→ Handle queue (if service has queue)
  │     │     • Wait up to queueTimeout
  │     │     • If exceeded, abort and retry with new account
  │     │
  │     └─→ Poll progress until 100%
  │           • Timeout: 30-60 minutes
  │
  ├─→ Download video
  │     • Save to configured download path
  │     • Rename to meaningful filename
  │
  ├─→ Extract metadata
  │     • Get title, description, outline from service
  │
  ├─→ AI enhance metadata (optional)
  │     • Generate SEO title
  │     • Generate SEO description
  │     • Generate tags
  │
  ├─→ Upload to YouTube
  │     │
  │     ├─→ Check if quota exceeded (skip if so)
  │     ├─→ Upload with metadata
  │     ├─→ Track quota usage
  │     └─→ Save YouTube URL to metadata
  │
  ├─→ Mark topic completed
  │     • Move from pending to completed
  │
  └─→ RETURN result (success/failure)
```

---

## Configuration Requirements

### Required Configuration

| Setting | Type | Description |
|---------|------|-------------|
| `workerCount` | number | Parallel workers (1-8 recommended) |
| `maxRetries` | number | Retry attempts for failed topics |
| `retryDelaySeconds` | number | Wait between retry attempts |
| `videoType` | enum | 'short' (~1 min) or 'long' (~10 min) |
| `downloadPath` | string | Where to save videos |

### Video Service Configuration

| Setting | Type | Description |
|---------|------|-------------|
| `videoService.type` | string | Which service to use |
| `videoService.credentials` | object | Service-specific auth |
| `videoService.promptTemplate` | string | Template with {TOPIC} placeholder |
| `videoService.timeouts.generation` | number | Max wait for video (ms) |
| `videoService.timeouts.queue` | number | Max wait in queue (ms) |

### YouTube Configuration

| Setting | Type | Description |
|---------|------|-------------|
| `youtube.enabled` | boolean | Enable YouTube upload |
| `youtube.credentialsPath` | string | OAuth client secret file |
| `youtube.tokensPath` | string | Where to save tokens |
| `youtube.defaultPrivacy` | enum | 'private', 'unlisted', 'public' |
| `youtube.defaultCategory` | string | Category ID |
| `youtube.stopOnQuota` | boolean | Stop when quota exceeded |
| `youtube.quotaFailureLimit` | number | Consecutive failures before stop |

### AI Configuration (Optional)

| Setting | Type | Description |
|---------|------|-------------|
| `ai.enabled` | boolean | Enable AI features |
| `ai.provider` | string | Which AI service |
| `ai.apiKey` | string | API authentication |
| `ai.baseUrl` | string | API endpoint |
| `ai.model` | string | Model to use |
| `ai.enhanceInput` | boolean | Enhance topics before generation |
| `ai.enhanceOutput` | boolean | Enhance metadata after generation |
| `ai.autoGenerate` | boolean | Generate topics when empty |
| `ai.topicsPerBatch` | number | Topics to generate per batch |

### Content Filter Configuration

| Setting | Type | Description |
|---------|------|-------------|
| `filter.enabled` | boolean | Enable content filtering |
| `filter.blockedKeywords` | string[] | Words to block |
| `filter.blockedPatterns` | regex[] | Patterns to block |
| `filter.allowedCategories` | string[] | Safe topic categories |

---

## Error Handling Requirements

### Retry Logic

| Error Type | Behavior |
|------------|----------|
| Email timeout | Retry topic (new account) |
| Verification failed | Retry topic (new account) |
| Queue timeout | Retry topic (new account) |
| Generation failed | Retry topic |
| Download failed | Retry topic |
| YouTube quota | Stop new work, wait 24h |
| YouTube other error | Log, retry later |
| AI API failure | Fall back to original content |
| Network error | Retry with backoff |

### Failure Tracking

- Track failed topics in separate file
- Include failure reason
- Support manual re-queue
- Orphaned videos (downloaded but not uploaded) should be uploaded on next run

### Graceful Degradation

- If AI unavailable: use original content
- If trending service unavailable: skip trends
- If quota exceeded: pause, don't crash
- If worker fails: continue with others

---

## Content Safety Requirements

### Blocked Content Categories

The system MUST filter out topics containing:

1. **Political Content**
   - Politicians, political parties, elections
   - Government policies, laws, regulations
   - Political debates, controversies

2. **War & Conflict**
   - Wars, invasions, military actions
   - Terrorism, extremism
   - Genocide, ethnic cleansing

3. **Controversial Social Issues**
   - Divisive social debates
   - Religious conflicts
   - Culture war topics

4. **Conspiracy Theories**
   - Misinformation
   - Conspiracy content
   - Pseudo-science presented as fact

5. **Hate Speech**
   - Racism, discrimination
   - Targeting individuals or groups
   - Extremist content

### Safe Content Categories

The system SHOULD prefer topics about:

- Technology, AI, innovation
- Science, space, discoveries
- Sustainability, clean energy
- Health, wellness (non-controversial)
- Education, tutorials
- Entertainment, creativity

### Implementation Requirements

- Filter BEFORE processing (don't waste resources)
- Filter AI-generated topics too
- Log blocked topics for review
- Allow filter customization

---

## Deployment Requirements

### Local Development

- Node.js 18+ or equivalent runtime
- Browser automation capability (Puppeteer, Playwright, Selenium)
- File system access for downloads
- Network access to external services

### Container Deployment

- Headless browser support required
- Shared memory for browser (1GB+ recommended)
- Volume mounts for:
  - Topic files (input)
  - Downloaded videos (output)
  - Credentials (secrets)
  - Logs
- Resource limits: 2GB+ RAM recommended

### Environment Variables

```bash
# Required
VIDEO_SERVICE_API_KEY=xxx
YOUTUBE_CLIENT_ID=xxx
YOUTUBE_CLIENT_SECRET=xxx

# Optional
AI_API_KEY=xxx
AI_BASE_URL=xxx
TRENDING_API_KEY=xxx
```

### Health Checks

- Worker count and status
- Queue size
- Last successful upload
- YouTube quota remaining (estimated)
- Service connectivity

---

## Implementation Freedom

### Your Developers May Choose:

#### Temporary Email Service
- Any disposable email API
- Self-hosted solution
- SMS verification alternative (if video service supports)

#### Video Generation Platform
- Any AI video generation service
- Consider: pricing, quality, API availability, generation speed
- May require browser automation (Puppeteer/Playwright) or pure API

#### AI Provider
- OpenAI, Anthropic, Google, local models, etc.
- Any OpenAI-compatible API works with minimal changes
- Can use different models for different tasks

#### Trending Topics Source
- Any news/trends API
- Web scraping
- Social media APIs
- Multiple sources combined

#### Programming Language
- Node.js (reference implementation)
- Python (popular for automation)
- Go (good for concurrency)
- Any language with browser automation and HTTP support

#### Browser Automation
- Puppeteer (Chromium)
- Playwright (multi-browser)
- Selenium
- Custom HTTP-based approach (if service has API)

#### Storage
- Local filesystem
- Cloud storage (S3, GCS, etc.)
- Database for metadata

#### Orchestration
- Simple script loop
- Message queue (Redis, RabbitMQ)
- Kubernetes jobs
- Serverless functions

### Constraints to Maintain:

1. **YouTube API is mandatory** - It's the target platform
2. **Content filtering is mandatory** - Prevent inappropriate content
3. **Parallel processing is expected** - Single-threaded is too slow
4. **Retry logic is required** - Services fail, network fails
5. **Quota handling is required** - YouTube has strict limits
6. **Continuous operation is expected** - Should run unattended

---

## Success Criteria

A successful implementation should:

1. **Generate videos autonomously** from text topics
2. **Upload to YouTube** with proper metadata
3. **Handle failures gracefully** with retries
4. **Respect YouTube quota** and pause when exceeded
5. **Filter inappropriate content** before processing
6. **Run continuously** with minimal intervention
7. **Process multiple videos in parallel** for efficiency
8. **Support topic generation** when queue is empty

---

## Appendix: Reference Prompts

### Video Generation Prompt Template (Long)

```
Create a 10 minutes video for YouTube about {TOPIC}

Settings:
- Use only royalty-free stock media
- Background music: soft and slow
- No subtitles
- Use royalty-free audio library
- Male narrator with clear American accent
```

### Video Generation Prompt Template (Short)

```
Create a 1 minute portrait video for YouTube Shorts about {TOPIC}

Settings:
- Use only royalty-free stock media
- Background music: upbeat and engaging
- Add bold subtitles with animation
- Use royalty-free audio library
- Fast-paced editing
```

### Topic Generation Prompt

```
Generate {COUNT} unique YouTube video topic ideas.

Requirements:
- Topics about: technology, science, sustainability, innovation
- Forward-looking and relevant for current year
- Specific and compelling (not generic)
- Positive, educational, entertaining

Restrictions:
- NO political content
- NO controversial social issues
- NO war, conflict, violence
- NO conspiracy theories
- NO content targeting individuals

Format: One topic per line, no numbering.
```

### Metadata Enhancement Prompt

```
Given this video information, create SEO-optimized metadata:

Title: {ORIGINAL_TITLE}
Description: {ORIGINAL_DESCRIPTION}
Topic: {TOPIC}

Generate:
1. New title (max 60 chars, front-load keywords)
2. New description (500-1500 chars, include timestamps if possible)
3. Tags (15-20, mix of broad and specific)

Be compelling but not clickbait.
```

---

*This specification defines WHAT the system should do, not HOW to implement it. Your developers have freedom to choose platforms, APIs, languages, and architectures that best fit your needs.*
