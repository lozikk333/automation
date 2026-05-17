'use client'

import React, { useState } from 'react'
import { AlertCircle, Check, Copy, Eye, EyeOff, Loader2, Plus, RotateCcw } from 'lucide-react'

interface FormField {
  name: string
  label: string
  type: 'text' | 'email' | 'password' | 'checkbox' | 'select'
  required: boolean
  placeholder?: string
  help?: string
  default?: boolean | string
}

interface WebsiteTypeOption {
  value: string
  label: string
  description: string
  icon: string
  fields: FormField[]
}

export function AddWebsiteModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [step, setStep] = useState<'type' | 'form' | 'success'>('type')
  const [selectedType, setSelectedType] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const [showPassword, setShowPassword] = useState<Record<string, boolean>>({})
  const [generatedApiKey, setGeneratedApiKey] = useState<string>('')
  const [copiedField, setCopiedField] = useState<string>('')

  const [formData, setFormData] = useState<Record<string, any>>({
    name: '',
    base_url: '',
    site_type: 'wordpress',
    username: '',
    password: '',
    publish_endpoint: '',
    api_key: '',
    api_enabled: true,
    pin_template: 'u1_u2_white_band',
    publish_status: 'draft',
  })

  const websiteTypes: WebsiteTypeOption[] = [
    {
      value: 'wordpress',
      label: 'WordPress',
      description: 'Publish to existing WordPress blog',
      icon: '📝',
      fields: [
        {
          name: 'username',
          label: 'WordPress Username or Email',
          type: 'text',
          required: true,
          placeholder: 'admin@example.com',
          help: 'WordPress user with upload permissions',
        },
        {
          name: 'password',
          label: 'Application Password',
          type: 'password',
          required: true,
          placeholder: 'xxxx xxxx xxxx xxxx xxxx xxxx',
          help: 'Generate at WordPress Settings → Apps Passwords',
        },
      ],
    },
    {
      value: 'html_static',
      label: 'HTML Static Site',
      description: 'Publish to static HTML with secure API',
      icon: '🌐',
      fields: [
        {
          name: 'publish_endpoint',
          label: 'Publish Endpoint (optional)',
          type: 'text',
          required: false,
          placeholder: 'https://example.com/internal-api/publish',
          help: 'Auto-generated if left empty',
        },
        {
          name: 'api_key',
          label: 'API Key (optional)',
          type: 'password',
          required: false,
          placeholder: 'Auto-generated if left empty',
          help: 'Secure token for publishing',
        },
        {
          name: 'api_enabled',
          label: 'Enable Publishing API',
          type: 'checkbox',
          required: false,
          default: true,
          help: 'Allow automated publishing',
        },
      ],
    },
  ]

  const currentType = websiteTypes.find((t) => t.value === formData.site_type)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, type, value, checked } = e.target as any
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))
    setError('')
  }

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text)
    setCopiedField(field)
    setTimeout(() => setCopiedField(''), 2000)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const payload = {
        name: formData.name.trim(),
        base_url: formData.base_url.trim(),
        site_type: formData.site_type,
        ...(formData.site_type === 'wordpress' && {
          username: formData.username.trim(),
          password: formData.password.trim(),
        }),
        ...(formData.site_type === 'html_static' && {
          publish_endpoint: formData.publish_endpoint.trim() || undefined,
          api_key: formData.api_key.trim() || undefined,
          api_enabled: formData.api_enabled,
        }),
        pin_template: formData.pin_template,
        publish_status: formData.publish_status,
      }

      const response = await fetch('/api/websites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      const result = await response.json()

      if (!response.ok) {
        throw new Error(result.detail || 'Failed to create website')
      }

      if (formData.site_type === 'html_static') {
        setGeneratedApiKey(result.api_key || '')
        setStep('success')
      } else {
        setStep('success')
      }

      setTimeout(() => {
        onSuccess()
        onClose()
      }, 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      setLoading(false)
    }
  }

  // Type Selection Step
  if (step === 'type') {
    return (
      <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-96 overflow-y-auto">
          <div className="p-8">
            <h2 className="text-2xl font-bold text-charcoal mb-2">Add Website</h2>
            <p className="text-secondary mb-8">Select the type of website to integrate</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              {websiteTypes.map((type) => (
                <button
                  key={type.value}
                  onClick={() => {
                    setFormData((prev) => ({ ...prev, site_type: type.value }))
                    setStep('form')
                  }}
                  className={`p-6 rounded-xl border-2 transition-all text-left ${
                    formData.site_type === type.value
                      ? 'border-gold bg-warm'
                      : 'border-charcoal/10 hover:border-gold'
                  }`}
                >
                  <div className="text-3xl mb-2">{type.icon}</div>
                  <h3 className="font-bold text-charcoal mb-1">{type.label}</h3>
                  <p className="text-sm text-secondary">{type.description}</p>
                </button>
              ))}
            </div>

            <div className="flex justify-end gap-3">
              <button
                onClick={onClose}
                className="px-6 py-2 rounded-lg border border-charcoal text-charcoal hover:bg-charcoal/5 transition"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Form Step
  if (step === 'form') {
    return (
      <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-screen overflow-y-auto">
          <div className="p-8">
            <h2 className="text-2xl font-bold text-charcoal mb-1">Add {currentType?.label} Website</h2>
            <p className="text-secondary mb-6">{currentType?.description}</p>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Common Fields */}
              <div>
                <label className="block text-sm font-medium text-charcoal mb-2">Website Name *</label>
                <input
                  type="text"
                  name="name"
                  required
                  placeholder="My Recipe Blog"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 border border-charcoal/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-gold/50"
                />
                <p className="text-xs text-secondary mt-1">Display name for this website</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-charcoal mb-2">Website URL *</label>
                <input
                  type="text"
                  name="base_url"
                  required
                  placeholder="https://example.com"
                  value={formData.base_url}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 border border-charcoal/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-gold/50"
                />
                <p className="text-xs text-secondary mt-1">Full URL including protocol (http:// or https://)</p>
              </div>

              {/* WordPress Fields */}
              {formData.site_type === 'wordpress' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-charcoal mb-2">
                      WordPress Username or Email *
                    </label>
                    <input
                      type="text"
                      name="username"
                      required
                      placeholder="admin@example.com"
                      value={formData.username}
                      onChange={handleInputChange}
                      className="w-full px-4 py-2 border border-charcoal/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-gold/50"
                    />
                    <p className="text-xs text-secondary mt-1">Account with upload permissions</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-charcoal mb-2">
                      Application Password *
                    </label>
                    <div className="relative">
                      <input
                        type={showPassword.password ? 'text' : 'password'}
                        name="password"
                        required
                        placeholder="xxxx xxxx xxxx xxxx xxxx xxxx"
                        value={formData.password}
                        onChange={handleInputChange}
                        className="w-full px-4 py-2 border border-charcoal/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-gold/50"
                      />
                      <button
                        type="button"
                        onClick={() =>
                          setShowPassword((prev) => ({ ...prev, password: !prev.password }))
                        }
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-secondary hover:text-charcoal"
                      >
                        {showPassword.password ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                    <p className="text-xs text-secondary mt-1">
                      Generate at WordPress Settings → Apps Passwords
                    </p>
                  </div>
                </>
              )}

              {/* HTML Static Fields */}
              {formData.site_type === 'html_static' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-charcoal mb-2">
                      Publish Endpoint (optional)
                    </label>
                    <input
                      type="text"
                      name="publish_endpoint"
                      placeholder="https://example.com/internal-api/publish"
                      value={formData.publish_endpoint}
                      onChange={handleInputChange}
                      className="w-full px-4 py-2 border border-charcoal/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-gold/50"
                    />
                    <p className="text-xs text-secondary mt-1">Auto-generated to website_url/internal-api/publish</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-charcoal mb-2">API Key (optional)</label>
                    <div className="relative">
                      <input
                        type={showPassword.api_key ? 'text' : 'password'}
                        name="api_key"
                        placeholder="Auto-generated if empty"
                        value={formData.api_key}
                        onChange={handleInputChange}
                        className="w-full px-4 py-2 border border-charcoal/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-gold/50"
                      />
                      <button
                        type="button"
                        onClick={() =>
                          setShowPassword((prev) => ({ ...prev, api_key: !prev.api_key }))
                        }
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-secondary hover:text-charcoal"
                      >
                        {showPassword.api_key ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                    <p className="text-xs text-secondary mt-1">Secure token generated if not provided</p>
                  </div>

                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      name="api_enabled"
                      checked={formData.api_enabled}
                      onChange={handleInputChange}
                      className="w-4 h-4 rounded accent-gold"
                    />
                    <span className="text-sm font-medium text-charcoal">Enable Publishing API</span>
                  </label>
                </>
              )}

              {/* Error Display */}
              {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex gap-3">
                  <AlertCircle size={18} className="text-red-600 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              )}

              {/* Buttons */}
              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setStep('type')}
                  disabled={loading}
                  className="px-6 py-2 rounded-lg border border-charcoal text-charcoal hover:bg-charcoal/5 disabled:opacity-50"
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={loading || !formData.name.trim() || !formData.base_url.trim()}
                  className="px-6 py-2 bg-charcoal text-white rounded-lg hover:bg-charcoal/90 disabled:opacity-50 flex items-center gap-2"
                >
                  {loading ? (
                    <>
                      <Loader2 size={18} className="animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Plus size={18} />
                      Create Website
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    )
  }

  // Success Step
  if (step === 'success') {
    return (
      <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full">
          <div className="p-8 text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Check size={32} className="text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-charcoal mb-2">Website Created Successfully!</h2>

            {generatedApiKey && (
              <div className="mt-8 p-6 bg-warm rounded-xl border border-gold text-left">
                <p className="text-sm font-medium text-charcoal mb-3">Your API Key</p>
                <div className="bg-white border border-charcoal/10 rounded-lg p-4 flex items-center justify-between gap-2">
                  <code className="font-mono text-sm text-secondary flex-1 truncate">{generatedApiKey}</code>
                  <button
                    onClick={() => copyToClipboard(generatedApiKey, 'api_key')}
                    className="p-2 hover:bg-charcoal/5 rounded transition flex-shrink-0"
                  >
                    {copiedField === 'api_key' ? (
                      <Check size={18} className="text-green-600" />
                    ) : (
                      <Copy size={18} className="text-secondary" />
                    )}
                  </button>
                </div>
                <p className="text-xs text-secondary mt-3">
                  Save this key in a safe place. You can regenerate it later if needed.
                </p>
              </div>
            )}

            <p className="text-secondary mt-6">Redirecting to websites list...</p>
          </div>
        </div>
      </div>
    )
  }

  return null
}

export default AddWebsiteModal
