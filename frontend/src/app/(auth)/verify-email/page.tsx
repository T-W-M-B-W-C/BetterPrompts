'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { useToast } from '@/hooks/use-toast'
import { authService } from '@/lib/api/services'
import { Loader2, Mail, CheckCircle, AlertCircle, ArrowRight } from 'lucide-react'

export default function VerifyEmailPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { toast } = useToast()
  
  const [isLoading, setIsLoading] = useState(false)
  const [isResending, setIsResending] = useState(false)
  const [isVerified, setIsVerified] = useState(false)
  const [error, setError] = useState('')
  const [code, setCode] = useState(['', '', '', '', '', ''])
  const [resendTimer, setResendTimer] = useState(0)
  const [userEmail, setUserEmail] = useState('')
  
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])
  
  // Check for token in URL
  useEffect(() => {
    const token = searchParams.get('token')
    const email = searchParams.get('email')
    
    if (email) {
      setUserEmail(email)
    }
    
    if (token) {
      // Auto-verify with token
      handleTokenVerification(token)
    }
  }, [searchParams])
  
  // Handle resend timer
  useEffect(() => {
    if (resendTimer > 0) {
      const timer = setTimeout(() => setResendTimer(resendTimer - 1), 1000)
      return () => clearTimeout(timer)
    }
  }, [resendTimer])
  
  const handleTokenVerification = async (token: string) => {
    setIsLoading(true)
    setError('')
    
    try {
      await authService.verifyEmail({ token })
      setIsVerified(true)
      toast({
        title: 'Email verified!',
        description: 'Your email has been successfully verified.',
      })
    } catch (err: any) {
      console.error('Token verification error:', err)
      setError(err.response?.data?.error || 'Invalid or expired verification link')
    } finally {
      setIsLoading(false)
    }
  }
  
  const handleCodeChange = (index: number, value: string) => {
    // Only allow alphanumeric characters
    const sanitized = value.replace(/[^a-zA-Z0-9]/g, '').toUpperCase()
    
    if (sanitized.length <= 1) {
      const newCode = [...code]
      newCode[index] = sanitized
      setCode(newCode)
      
      // Auto-focus next input
      if (sanitized && index < 5) {
        inputRefs.current[index + 1]?.focus()
      }
    }
  }
  
  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
  }
  
  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault()
    const pastedData = e.clipboardData.getData('text').replace(/[^a-zA-Z0-9]/g, '').toUpperCase()
    const chars = pastedData.slice(0, 6).split('')
    
    const newCode = [...code]
    chars.forEach((char, i) => {
      if (i < 6) newCode[i] = char
    })
    setCode(newCode)
    
    // Focus the next empty input or the last input
    const nextEmpty = newCode.findIndex(c => !c)
    const focusIndex = nextEmpty === -1 ? 5 : nextEmpty
    inputRefs.current[focusIndex]?.focus()
  }
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    const verificationCode = code.join('')
    if (verificationCode.length !== 6) {
      setError('Please enter the complete verification code')
      return
    }
    
    setIsLoading(true)
    setError('')
    
    try {
      await authService.verifyEmail({ 
        code: verificationCode,
        email: userEmail || localStorage.getItem('registrationEmail') || ''
      })
      
      setIsVerified(true)
      toast({
        title: 'Email verified!',
        description: 'Your email has been successfully verified.',
      })
    } catch (err: any) {
      console.error('Code verification error:', err)
      setError(err.response?.data?.error || 'Invalid verification code')
    } finally {
      setIsLoading(false)
    }
  }
  
  const handleResendEmail = async () => {
    if (resendTimer > 0) return
    
    setIsResending(true)
    setError('')
    
    try {
      const email = userEmail || localStorage.getItem('registrationEmail')
      if (!email) {
        setError('Email address not found. Please register again.')
        return
      }
      
      await authService.resendVerification({ email })
      
      toast({
        title: 'Verification email sent!',
        description: 'Please check your inbox for the new verification code.',
      })
      
      // Set 60 second cooldown
      setResendTimer(60)
      
      // Clear the code inputs
      setCode(['', '', '', '', '', ''])
      inputRefs.current[0]?.focus()
    } catch (err: any) {
      console.error('Resend error:', err)
      setError(err.response?.data?.error || 'Failed to resend verification email')
    } finally {
      setIsResending(false)
    }
  }
  
  const handleContinue = () => {
    // Clear stored email
    localStorage.removeItem('registrationEmail')
    router.push('/dashboard')
  }
  
  if (isVerified) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-muted/20 px-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto w-16 h-16 bg-green-100 dark:bg-green-900/20 rounded-full flex items-center justify-center mb-4">
              <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
            </div>
            <CardTitle className="text-2xl font-bold">Email Verified!</CardTitle>
            <CardDescription>
              Your email has been successfully verified. You can now access all features.
            </CardDescription>
          </CardHeader>
          <CardFooter>
            <Button 
              onClick={handleContinue} 
              className="w-full"
              size="lg"
            >
              Continue to Dashboard
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardFooter>
        </Card>
      </div>
    )
  }
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-muted/20 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
            <Mail className="w-8 h-8 text-primary" />
          </div>
          <CardTitle className="text-2xl font-bold">Verify your email</CardTitle>
          <CardDescription>
            We've sent a verification code to your email address. 
            Please enter the 6-digit code below.
          </CardDescription>
        </CardHeader>
        
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-6">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            
            <div>
              <p className="text-sm text-muted-foreground mb-4 text-center">
                Enter verification code
              </p>
              <div className="flex gap-2 justify-center">
                {code.map((digit, index) => (
                  <Input
                    key={index}
                    ref={el => inputRefs.current[index] = el}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleCodeChange(index, e.target.value)}
                    onKeyDown={(e) => handleKeyDown(index, e)}
                    onPaste={index === 0 ? handlePaste : undefined}
                    className="w-12 h-12 text-center text-lg font-semibold"
                    disabled={isLoading}
                    autoFocus={index === 0}
                  />
                ))}
              </div>
            </div>
            
            <div className="text-center">
              <p className="text-sm text-muted-foreground mb-2">
                Didn't receive the email?
              </p>
              <Button
                type="button"
                variant="link"
                onClick={handleResendEmail}
                disabled={isResending || resendTimer > 0}
                className="text-sm"
              >
                {isResending ? (
                  <>
                    <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                    Sending...
                  </>
                ) : resendTimer > 0 ? (
                  `Resend in ${resendTimer}s`
                ) : (
                  'Resend verification email'
                )}
              </Button>
            </div>
          </CardContent>
          
          <CardFooter>
            <Button
              type="submit"
              className="w-full"
              disabled={isLoading || code.some(c => !c)}
              size="lg"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Verifying...
                </>
              ) : (
                'Verify Email'
              )}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}