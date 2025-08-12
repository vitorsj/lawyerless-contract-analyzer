# 🏠 LM Studio Setup Guide for Lawyerless

## Quick Start with LM Studio

### 1. Install LM Studio

1. **Download LM Studio**: Visit [https://lmstudio.ai](https://lmstudio.ai)
2. **Install the Application**: Follow platform-specific installation instructions
3. **Launch LM Studio**: Open the application

### 2. Download a Model

1. **Browse Models**: Go to the "Discover" tab in LM Studio
2. **Recommended Models for Portuguese Contracts**:
   - **Llama 3.1 8B Instruct** (Good balance of speed and quality)
   - **Llama 3.1 70B Instruct** (Best quality, requires more RAM)
   - **Mistral 7B Instruct** (Fast and efficient)
   - **CodeLlama 34B** (Good for structured output)

3. **Download**: Click download button and wait for completion

### 3. Start Local Server

1. **Load Model**: Go to "Chat" tab and select your downloaded model
2. **Start Server**: Go to "Local Server" tab
3. **Configure Settings**:
   - **Port**: 1234 (default, matches Lawyerless config)
   - **CORS**: Enable for web requests
   - **Model**: Select your loaded model
4. **Start Server**: Click "Start Server" button

### 4. Configure Lawyerless

Update your `.env` file:

```bash
# Switch to LM Studio provider
LLM_PROVIDER=lm_studio

# LM Studio Configuration (Local LLM Server)
LM_STUDIO_MODEL=llama-3.1-8b-instruct
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_TIMEOUT=180
```

### 5. Test the Connection

```bash
# Test if LM Studio is running
curl http://localhost:1234/v1/models

# Test contract analysis with LM Studio
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "file=@your-contract.pdf" \
  -F "perspectiva=fundador" \
  -F "llm_provider=lm_studio"
```

## 🔧 Troubleshooting

### Model Not Loading
- **Issue**: Model fails to load or server won't start
- **Solution**: Check available RAM - larger models need more memory
- **Recommendation**: Start with smaller models like Llama 3.1 8B

### Connection Refused
- **Issue**: `curl: (7) Failed to connect to localhost port 1234`
- **Solutions**:
  - Ensure LM Studio server is running (green indicator)
  - Check port configuration matches (default: 1234)
  - Verify CORS is enabled in LM Studio settings

### Slow Responses
- **Issue**: Analysis takes very long
- **Solutions**:
  - Use smaller models (7B-8B parameters)
  - Increase `LM_STUDIO_TIMEOUT` in .env
  - Consider GPU acceleration if available
  - Close other resource-intensive applications

### Model Download Failed
- **Issue**: Download interrupted or failed
- **Solutions**:
  - Check internet connection
  - Free up disk space
  - Try downloading smaller models first
  - Restart LM Studio and retry

## 📊 Performance Guidelines

### Model Size vs Performance

| Model Size | RAM Required | Speed | Quality | Best For |
|------------|-------------|--------|---------|----------|
| 7B-8B      | 8-12 GB     | Fast   | Good    | Development, Testing |
| 13B-14B    | 16-20 GB    | Medium | Better  | Production (small scale) |
| 30B-34B    | 32-48 GB    | Slow   | Great   | High-quality analysis |
| 70B+       | 64+ GB      | Very Slow | Excellent | Research, Best results |

### Optimization Tips

1. **GPU Acceleration**: Enable in LM Studio settings if you have a compatible GPU
2. **Model Quantization**: Use quantized models (Q4, Q8) for better performance
3. **Context Length**: Adjust context window based on typical contract size
4. **Batch Size**: Configure for your hardware capabilities
5. **Temperature**: Lower values (0.1-0.3) for more consistent legal analysis

## 🔐 Security Benefits

### Data Privacy
- **Local Processing**: Contracts never leave your machine
- **No Cloud Dependency**: Works entirely offline
- **No Logging**: LM Studio doesn't log your prompts
- **Custom Models**: Train on your specific contract types

### Compliance
- **GDPR Compliant**: Data processing stays local
- **SOC 2 Ready**: No third-party data sharing
- **Industry Standards**: Meets strict privacy requirements
- **Audit Trail**: Full control over processing logs

## 🚀 Advanced Configuration

### Custom Model Training
1. **Prepare Dataset**: Collect your contract analysis examples
2. **Fine-tuning**: Use tools like LoRA for model customization
3. **Integration**: Load custom models into LM Studio
4. **Testing**: Validate performance against known contracts

### Multi-Model Setup
1. **Different Models**: Use different models for different contract types
2. **Load Balancing**: Distribute requests across multiple instances
3. **Fallback Chain**: Configure automatic fallbacks if one model fails
4. **Performance Monitoring**: Track response times and quality metrics

The local LM Studio setup provides enterprise-grade privacy with the flexibility of open-source models! 🔒