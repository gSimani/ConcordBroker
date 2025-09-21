import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Phone, Lock, ArrowRight } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { api } from '@/api/client'
import { useAuth } from '@/hooks/use-auth'

export function PhoneVerify() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [step, setStep] = useState<'phone' | 'verify'>('phone')
  const [phone, setPhone] = useState('')
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [demoMode, setDemoMode] = useState(false)
  const [demoCode, setDemoCode] = useState('')

  const formatPhone = (value: string) => {
    // Remove all non-digits
    const digits = value.replace(/\D/g, '')
    
    // Format as (XXX) XXX-XXXX
    if (digits.length <= 3) {
      return digits
    } else if (digits.length <= 6) {
      return `(${digits.slice(0, 3)}) ${digits.slice(3)}`
    } else {
      return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6, 10)}`
    }
  }

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatPhone(e.target.value)
    setPhone(formatted)
  }

  const sendCode = async () => {
    setLoading(true)
    setError('')
    
    try {
      const cleanPhone = phone.replace(/\D/g, '')
      if (cleanPhone.length !== 10) {
        throw new Error('Please enter a valid 10-digit phone number')
      }
      
      const response = await api.sendVerificationCode(cleanPhone)
      
      if (response.success) {
        setStep('verify')
        if (response.demo_mode) {
          setDemoMode(true)
          // Extract demo code from message
          const match = response.message?.match(/code (\d+)/)
          if (match) {
            setDemoCode(match[1])
          }
        }
      } else {
        setError(response.message || 'Failed to send verification code')
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const verifyCode = async () => {
    setLoading(true)
    setError('')
    
    try {
      const cleanPhone = phone.replace(/\D/g, '')
      const response = await api.verifyCode(cleanPhone, code)
      
      if (response.success && response.access_token) {
        // Store token and redirect
        const user = {
          id: response.user_id || cleanPhone,
          email: response.email || '',
        }
        login(response.access_token, response.refresh_token || '', user)
        navigate('/dashboard')
      } else {
        setError(response.message || 'Invalid verification code')
      }
    } catch (err: any) {
      setError(err.message || 'Verification failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold">ConcordBroker</CardTitle>
          <CardDescription>
            {step === 'phone' 
              ? 'Enter your phone number to continue'
              : 'Enter the verification code sent to your phone'
            }
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          
          {demoMode && demoCode && (
            <Alert>
              <AlertDescription>
                Demo Mode: Use code <strong>{demoCode}</strong>
              </AlertDescription>
            </Alert>
          )}
          
          {step === 'phone' ? (
            <>
              <div className="space-y-2">
                <Label htmlFor="phone" className="flex items-center gap-2">
                  <Phone className="h-4 w-4" />
                  Phone Number
                </Label>
                <Input
                  id="phone"
                  type="tel"
                  placeholder="(555) 123-4567"
                  value={phone}
                  onChange={handlePhoneChange}
                  maxLength={14}
                />
              </div>
              
              <Button 
                className="w-full" 
                onClick={sendCode}
                disabled={loading || phone.replace(/\D/g, '').length !== 10}
              >
                {loading ? 'Sending...' : 'Send Verification Code'}
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </>
          ) : (
            <>
              <div className="text-center text-sm text-muted-foreground mb-4">
                Verification code sent to {phone}
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="code" className="flex items-center gap-2">
                  <Lock className="h-4 w-4" />
                  Verification Code
                </Label>
                <Input
                  id="code"
                  type="text"
                  placeholder="123456"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  maxLength={6}
                  className="text-center text-2xl tracking-widest"
                />
              </div>
              
              <Button 
                className="w-full" 
                onClick={verifyCode}
                disabled={loading || code.length !== 6}
              >
                {loading ? 'Verifying...' : 'Verify & Login'}
              </Button>
              
              <Button
                variant="outline"
                className="w-full"
                onClick={() => {
                  setStep('phone')
                  setCode('')
                  setError('')
                }}
              >
                Change Phone Number
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}