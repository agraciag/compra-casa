# Scraping Approach Guidelines

## Ethical Web Scraping Principles

### Rate Limiting
- Implement delays between requests (minimum 1-2 seconds between requests)
- Use random intervals to appear more human-like
- Respect server load during peak hours
- Monitor response times and adjust accordingly

### Headers and Identification
- Use realistic user-agent strings
- Rotate user-agents periodically
- Include appropriate accept headers
- Respect cookies and session management

### Robots.txt Compliance
- Always check and respect robots.txt files
- Follow crawl-delay directives
- Avoid disallowed paths
- Check for updates periodically

## Technical Implementation

### Request Throttling
```python
import time
import random

def make_request(url):
    # Random delay between requests
    time.sleep(random.uniform(1.5, 3.0))
    
    # Make request with appropriate headers
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    response = requests.get(url, headers=headers)
    return response
```

### Session Management
- Use sessions to maintain cookies
- Handle redirects appropriately
- Implement retry mechanisms with exponential backoff
- Log failed requests for debugging

### Error Handling
- Implement proper exception handling
- Distinguish between temporary and permanent errors
- Adjust scraping speed based on error rates
- Maintain detailed logs for troubleshooting

## Site-Specific Considerations

### Idealista
- Limit requests to avoid triggering anti-bot measures
- Respect pagination limits
- Monitor for CAPTCHA challenges
- Implement proxy rotation if needed

### Fotocasa
- Follow their API terms if available
- Avoid aggressive crawling patterns
- Respect geographic filtering
- Monitor for rate limiting responses

### Official Sources (Penotariado, etc.)
- These may have more restrictive policies
- Limit frequency of requests significantly
- Consider using official APIs if available
- Respect data usage terms

## Monitoring and Maintenance

### Logging
- Track request rates and success/failure ratios
- Monitor for changes in site structure
- Log IP address blocks or restrictions
- Record performance metrics

### Adaptive Behavior
- Adjust scraping patterns based on site responses
- Implement fallback strategies for blocked IPs
- Update selectors when sites change structure
- Scale back activity if issues arise

## Legal Compliance
- Ensure compliance with Terms of Service
- Respect copyright and data usage rights
- Consider GDPR implications for personal data
- Document data retention and deletion policies