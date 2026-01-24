# Batch Upload Troubleshooting Guide

## Common Reasons for Upload Failures

### 1. YouTube API Quota Exceeded ⚠️
**Symptoms**: First few videos succeed, then all fail
**Cause**: YouTube Data API v3 has daily quota limits
**Quota Limits (Free Tier)**:
- 10,000 quota units per day
- Each video upload costs ~1,600 units
- **Maximum ~6 uploads per day**

**Solution**:
```powershell
# Wait 24 hours for quota reset, OR
# Request quota increase from Google Cloud Console
# OR split batch into smaller runs
```

### 2. OAuth Token Expiration
**Symptoms**: "401 Unauthorized" or "invalid_grant" errors
**Cause**: Token expires during long batch runs

**Solution**:
```powershell
# Delete token and re-authenticate
rm config/token.json
python main.py "Test Topic"  # Re-authenticate
python batch_processor.py    # Try again
```

### 3. Content Policy Violations
**Symptoms**: Specific topics fail consistently
**Cause**: YouTube flags sensitive content (Bitcoin, Medical, Climate)

**Solution**:
- Upload manually to review flags
- Modify scripts to be less controversial
- Check YouTube's community guidelines

### 4. Network/Timeout Issues
**Symptoms**: Random failures during upload
**Cause**: Poor internet connection or large file sizes

**Solution**:
- Check internet stability
- Reduce video quality if needed
- Retry failed topics

---

## How to Debug

### Step 1: Check Error Log
```powershell
# After batch run, check:
cat batch_errors.log
```

### Step 2: Check YouTube API Quota
1. Go to: https://console.cloud.google.com/
2. Navigate to: **APIs & Services** > **Quotas**
3. Search for: "YouTube Data API v3"
4. Check remaining quota

### Step 3: Test Individual Topics
```powershell
# Test one failed topic manually
python main.py "How Coffee Conquered the World"

# Check if it's a topic-specific issue
```

### Step 4: Verify Authentication
```powershell
# Check if token.json exists
ls config/token.json

# If expired, delete and re-auth
rm config/token.json
python main.py "Test"
```

---

## Quick Fixes

### Fix 1: Respect Daily Quota Limits
```yaml
# Edit topics.txt to process only 5-6 videos per day
# Run batch processor daily instead of all at once
```

### Fix 2: Add Retry Logic
The system already tracks failed topics. Re-run with only failures:

```powershell
# Create failed_topics.txt with only failed ones
python batch_processor.py  # Will process from topics.txt
```

### Fix 3: Increase Upload Timeout
If uploads timeout, increase the chunk upload timeout (advanced).

---

## Most Likely Issue for Your Case

**YouTube API Quota Exceeded**

You processed 10 topics:
- ✅ First 6 succeeded (used ~9,600 quota units)
- ❌ Last 4 failed (quota exhausted)

**Solution**:
1. Wait 24 hours for quota reset
2. Create a new file `remaining_topics.txt`:
   ```
   How Coffee Conquered the World
   The Story of Bitcoin
   Revolutionary Medical Breakthroughs
   Climate Change Solutions
   ```
3. Update `batch_processor.py` to use `remaining_topics.txt`
4. Run again tomorrow

OR request quota increase from Google Cloud Console (takes 2-3 days for approval).
