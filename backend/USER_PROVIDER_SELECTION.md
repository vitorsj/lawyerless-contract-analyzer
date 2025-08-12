# 🎛️ User LLM Provider Selection Guide

## Overview

Users can select their preferred LLM provider (OpenAI or LM Studio) at multiple levels, from global defaults to per-analysis overrides.

## 🌐 Selection Methods

### 1. **Global Default (System Level)**
**Location**: Server configuration (`.env` file)
```bash
LLM_PROVIDER=openai  # or lm_studio
```
**Who**: System administrator
**When**: Server startup/configuration
**Scope**: All users by default

### 2. **User Profile Settings (Recommended)**
**Location**: Frontend user settings/profile page
**Who**: Individual users
**When**: Account setup or settings change
**Scope**: All analyses for that user
**Implementation**: Store in user database/preferences

### 3. **Per-Analysis Selection (Most Flexible)**
**Location**: Analysis upload form
**Who**: User for each analysis
**When**: During contract upload
**Scope**: Single analysis only
**Implementation**: Dropdown/radio buttons in UI

### 4. **API Direct Selection (Developers)**
**Location**: API request parameters
**Who**: Developers/integrators
**When**: Each API call
**Scope**: Single API request
**Implementation**: `llm_provider` parameter

## 🎨 Frontend Implementation Ideas

### A. Analysis Upload Form
```html
<form id="contractAnalysisForm">
  <!-- File Upload -->
  <input type="file" name="contract" accept=".pdf" required>
  
  <!-- Perspective Selection -->
  <select name="perspectiva" required>
    <option value="fundador">Fundador</option>
    <option value="investidor">Investidor</option>
  </select>
  
  <!-- LLM Provider Selection -->
  <div class="provider-selection">
    <label>🤖 Escolha o Modelo de IA:</label>
    
    <div class="provider-option">
      <input type="radio" id="openai" name="llm_provider" value="openai" checked>
      <label for="openai">
        <div class="provider-card">
          <div class="provider-header">
            <span class="provider-icon">☁️</span>
            <span class="provider-name">OpenAI GPT-4</span>
            <span class="provider-badge cloud">Nuvem</span>
          </div>
          <div class="provider-details">
            <p>• Mais avançado e preciso</p>
            <p>• Processamento rápido</p>
            <p>• Requer conexão com internet</p>
            <p>• Custo por análise</p>
          </div>
        </div>
      </label>
    </div>
    
    <div class="provider-option">
      <input type="radio" id="lm_studio" name="llm_provider" value="lm_studio">
      <label for="lm_studio">
        <div class="provider-card">
          <div class="provider-header">
            <span class="provider-icon">🏠</span>
            <span class="provider-name">LM Studio Local</span>
            <span class="provider-badge local">Local</span>
          </div>
          <div class="provider-details">
            <p>• Totalmente privado</p>
            <p>• Sem custos adicionais</p>
            <p>• Funciona offline</p>
            <p>• Requer LM Studio instalado</p>
          </div>
        </div>
      </label>
    </div>
  </div>
  
  <button type="submit">Analisar Contrato</button>
</form>
```

### B. Provider Status Indicator
```html
<div class="provider-status-bar">
  <div class="current-provider">
    <span class="status-icon">🤖</span>
    <span>Modelo Atual: <strong id="currentProvider">OpenAI GPT-4</strong></span>
    <button class="change-provider-btn">Alterar</button>
  </div>
  
  <div class="provider-health">
    <div class="provider-indicator openai" data-status="healthy">
      <span class="indicator-dot green"></span>
      <span>OpenAI</span>
    </div>
    <div class="provider-indicator lm-studio" data-status="offline">
      <span class="indicator-dot red"></span>
      <span>LM Studio</span>
    </div>
  </div>
</div>
```

### C. User Settings Page
```html
<div class="settings-section">
  <h3>🤖 Preferências de IA</h3>
  
  <div class="setting-group">
    <label>Modelo Padrão para Análises</label>
    <select id="defaultProvider" class="form-control">
      <option value="openai">OpenAI GPT-4 (Nuvem)</option>
      <option value="lm_studio">LM Studio (Local)</option>
    </select>
    <small class="help-text">Você pode alterar isso para cada análise individual.</small>
  </div>
  
  <div class="setting-group">
    <label>
      <input type="checkbox" id="rememberProvider">
      Lembrar da minha escolha para próximas análises
    </label>
  </div>
  
  <div class="provider-comparison">
    <table class="comparison-table">
      <thead>
        <tr>
          <th>Característica</th>
          <th>OpenAI</th>
          <th>LM Studio</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Privacidade</td>
          <td>⚠️ Na nuvem</td>
          <td>✅ 100% local</td>
        </tr>
        <tr>
          <td>Custo</td>
          <td>💰 Por análise</td>
          <td>🆓 Gratuito</td>
        </tr>
        <tr>
          <td>Velocidade</td>
          <td>⚡ Muito rápido</td>
          <td>🐢 Depende do PC</td>
        </tr>
        <tr>
          <td>Qualidade</td>
          <td>🏆 Excelente</td>
          <td>👍 Boa</td>
        </tr>
        <tr>
          <td>Requisitos</td>
          <td>🌐 Internet</td>
          <td>💻 LM Studio</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
```

## 📱 Mobile/Responsive Design

### Quick Provider Toggle
```html
<div class="mobile-provider-toggle">
  <div class="toggle-label">🤖 Modelo de IA</div>
  <div class="toggle-switch">
    <input type="radio" name="provider" id="cloud" value="openai" checked>
    <label for="cloud" class="toggle-option">
      <span class="icon">☁️</span>
      <span class="text">Nuvem</span>
    </label>
    
    <input type="radio" name="provider" id="local" value="lm_studio">
    <label for="local" class="toggle-option">
      <span class="icon">🏠</span>
      <span class="text">Local</span>
    </label>
  </div>
</div>
```

## 🔧 JavaScript Implementation

### Provider Selection Logic
```javascript
class ProviderManager {
  constructor() {
    this.currentProvider = 'openai'; // default
    this.providerStatus = {};
    this.checkProviderStatus();
  }
  
  async checkProviderStatus() {
    try {
      const response = await fetch('/api/v1/llm/providers');
      const data = await response.json();
      
      data.providers.forEach(provider => {
        this.providerStatus[provider.provider] = provider.available;
        this.updateProviderUI(provider.provider, provider.available);
      });
    } catch (error) {
      console.error('Failed to check provider status:', error);
    }
  }
  
  setProvider(providerName) {
    if (!this.providerStatus[providerName]) {
      this.showProviderError(providerName);
      return false;
    }
    
    this.currentProvider = providerName;
    this.updateCurrentProviderUI();
    
    // Save to localStorage for persistence
    localStorage.setItem('preferredProvider', providerName);
    
    return true;
  }
  
  async analyzeContract(formData) {
    // Add provider selection to form data
    formData.append('llm_provider', this.currentProvider);
    
    try {
      const response = await fetch('/api/v1/analyze', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      this.handleAnalysisError(error);
      throw error;
    }
  }
  
  showProviderError(provider) {
    const messages = {
      'lm_studio': 'LM Studio não está rodando. Por favor, inicie o servidor local.',
      'openai': 'Não foi possível conectar com OpenAI. Verifique sua configuração.'
    };
    
    alert(messages[provider] || 'Provedor não disponível');
  }
  
  updateProviderUI(provider, available) {
    const element = document.querySelector(`.provider-indicator.${provider.replace('_', '-')}`);
    if (element) {
      element.dataset.status = available ? 'healthy' : 'offline';
      const dot = element.querySelector('.indicator-dot');
      dot.className = `indicator-dot ${available ? 'green' : 'red'}`;
    }
  }
  
  updateCurrentProviderUI() {
    const names = {
      'openai': 'OpenAI GPT-4',
      'lm_studio': 'LM Studio Local'
    };
    
    const element = document.getElementById('currentProvider');
    if (element) {
      element.textContent = names[this.currentProvider];
    }
  }
}

// Initialize provider manager
const providerManager = new ProviderManager();

// Load saved preference
const savedProvider = localStorage.getItem('preferredProvider');
if (savedProvider) {
  providerManager.setProvider(savedProvider);
}

// Form submission handler
document.getElementById('contractAnalysisForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const formData = new FormData(e.target);
  const selectedProvider = formData.get('llm_provider') || providerManager.currentProvider;
  
  if (!providerManager.setProvider(selectedProvider)) {
    return; // Provider error already shown
  }
  
  try {
    const result = await providerManager.analyzeContract(formData);
    handleAnalysisSuccess(result);
  } catch (error) {
    handleAnalysisError(error);
  }
});
```

## 🎯 User Experience Recommendations

### 1. **Smart Defaults**
- New users: Start with OpenAI (most reliable)
- Returning users: Remember last choice
- Enterprise users: Default to LM Studio (privacy)

### 2. **Clear Communication**
- Show provider status (online/offline) in real-time
- Explain tradeoffs clearly (privacy vs speed vs cost)
- Provide setup help for LM Studio

### 3. **Graceful Fallbacks**
- If selected provider fails, offer to switch
- Show estimated wait times for each provider
- Suggest optimal provider based on file size

### 4. **Progressive Disclosure**
- Basic users: Simple toggle (Cloud vs Local)
- Advanced users: Full provider details
- Developers: API documentation

## 🔄 Implementation Priority

### Phase 1: Basic Selection
1. Add provider radio buttons to analysis form
2. Implement JavaScript provider switching
3. Show basic provider status

### Phase 2: Enhanced UX
1. Add user preference storage
2. Real-time provider health checks
3. Provider comparison table

### Phase 3: Advanced Features
1. Smart provider recommendations
2. Usage analytics per provider
3. Cost tracking and budgets

This approach gives users full control while maintaining simplicity for casual users and power for advanced users! 🎛️