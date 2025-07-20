'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from '@/components/ui/use-toast'
import { Loader2, Save, User, Bell, Shield, Palette } from 'lucide-react'
import { useEnhanceStore } from '@/store/useEnhanceStore'
import { useUserStore } from '@/store/useUserStore'
import { Badge } from '@/components/ui/badge'

// Available techniques for preference selection
const AVAILABLE_TECHNIQUES = [
  { id: 'cot', name: 'Chain of Thought', description: 'Step-by-step reasoning' },
  { id: 'tot', name: 'Tree of Thoughts', description: 'Explore multiple reasoning paths' },
  { id: 'few_shot', name: 'Few-Shot Learning', description: 'Learn from examples' },
  { id: 'zero_shot', name: 'Zero-Shot Learning', description: 'Direct task completion' },
  { id: 'reflection', name: 'Self-Reflection', description: 'Critical analysis of outputs' },
  { id: 'decomposition', name: 'Task Decomposition', description: 'Break down complex tasks' },
  { id: 'analogical', name: 'Analogical Reasoning', description: 'Use comparisons and metaphors' },
  { id: 'recursive', name: 'Recursive Prompting', description: 'Iterative refinement' },
  { id: 'role_based', name: 'Role-Based Prompting', description: 'Expert persona adoption' },
  { id: 'emotional', name: 'Emotional Prompting', description: 'Incorporate emotional context' },
]

export default function SettingsPage() {
  const router = useRouter()
  const { user } = useUserStore()
  const { preferences: userPreferences, updatePreferences, togglePreferredTechnique } = useEnhanceStore()
  
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [activeTab, setActiveTab] = useState('general')

  // Local state for form
  const [formData, setFormData] = useState({
    preferredTechniques: userPreferences?.preferredTechniques || [],
    autoSuggest: userPreferences?.autoSuggest ?? true,
    saveHistory: userPreferences?.saveHistory ?? true,
    theme: userPreferences?.theme || 'system',
    emailNotifications: true,
    analyticsOptIn: true,
    complexityPreference: 'balanced',
    uiLanguage: 'en',
  })

  // Fetch user preferences on mount
  useEffect(() => {
    const fetchUserPreferences = async () => {
      if (!user) {
        router.push('/login')
        return
      }

      setLoading(true)
      try {
        const response = await fetch('/api/v1/auth/profile', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
        })

        if (!response.ok) {
          throw new Error('Failed to fetch user preferences')
        }

        const data = await response.json()
        if (data.data?.preferences) {
          const prefs = data.data.preferences
          setFormData({
            preferredTechniques: prefs.preferred_techniques || [],
            autoSuggest: prefs.auto_suggest ?? true,
            saveHistory: prefs.save_history ?? true,
            theme: prefs.ui_theme || 'system',
            emailNotifications: prefs.email_notifications ?? true,
            analyticsOptIn: prefs.analytics_opt_in ?? true,
            complexityPreference: prefs.complexity_preference || 'balanced',
            uiLanguage: prefs.ui_language || 'en',
          })
        }
      } catch (error) {
        console.error('Error fetching preferences:', error)
        toast({
          title: 'Error',
          description: 'Failed to load your preferences',
          variant: 'destructive',
        })
      } finally {
        setLoading(false)
      }
    }

    fetchUserPreferences()
  }, [user, router])

  // Handle technique toggle
  const handleTechniqueToggle = (techniqueId: string) => {
    setFormData(prev => ({
      ...prev,
      preferredTechniques: prev.preferredTechniques.includes(techniqueId)
        ? prev.preferredTechniques.filter(id => id !== techniqueId)
        : [...prev.preferredTechniques, techniqueId]
    }))
  }

  // Save preferences
  const handleSave = async () => {
    setSaving(true)
    try {
      const preferencesData = {
        preferred_techniques: formData.preferredTechniques,
        auto_suggest: formData.autoSuggest,
        save_history: formData.saveHistory,
        ui_theme: formData.theme,
        email_notifications: formData.emailNotifications,
        analytics_opt_in: formData.analyticsOptIn,
        complexity_preference: formData.complexityPreference,
        ui_language: formData.uiLanguage,
      }

      const response = await fetch('/api/v1/auth/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          preferences: preferencesData,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to save preferences')
      }

      // Update local store
      updatePreferences({
        preferredTechniques: formData.preferredTechniques,
        autoSuggest: formData.autoSuggest,
        saveHistory: formData.saveHistory,
        theme: formData.theme as 'light' | 'dark' | 'system',
      })

      toast({
        title: 'Success',
        description: 'Your preferences have been saved',
      })
    } catch (error) {
      console.error('Error saving preferences:', error)
      toast({
        title: 'Error',
        description: 'Failed to save your preferences',
        variant: 'destructive',
      })
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[600px]">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Settings</h1>
        <p className="text-muted-foreground">
          Manage your preferences and account settings
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="general" className="flex items-center gap-2">
            <User className="h-4 w-4" />
            General
          </TabsTrigger>
          <TabsTrigger value="techniques" className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Techniques
          </TabsTrigger>
          <TabsTrigger value="appearance" className="flex items-center gap-2">
            <Palette className="h-4 w-4" />
            Appearance
          </TabsTrigger>
          <TabsTrigger value="notifications" className="flex items-center gap-2">
            <Bell className="h-4 w-4" />
            Notifications
          </TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>General Preferences</CardTitle>
              <CardDescription>
                Configure your basic application preferences
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="auto-suggest">Auto-suggest techniques</Label>
                  <p className="text-sm text-muted-foreground">
                    Automatically suggest relevant techniques based on your input
                  </p>
                </div>
                <Switch
                  id="auto-suggest"
                  checked={formData.autoSuggest}
                  onCheckedChange={(checked) => 
                    setFormData(prev => ({ ...prev, autoSuggest: checked }))
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="save-history">Save prompt history</Label>
                  <p className="text-sm text-muted-foreground">
                    Keep a history of your enhanced prompts for future reference
                  </p>
                </div>
                <Switch
                  id="save-history"
                  checked={formData.saveHistory}
                  onCheckedChange={(checked) => 
                    setFormData(prev => ({ ...prev, saveHistory: checked }))
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="complexity">Complexity preference</Label>
                <Select
                  value={formData.complexityPreference}
                  onValueChange={(value) => 
                    setFormData(prev => ({ ...prev, complexityPreference: value }))
                  }
                >
                  <SelectTrigger id="complexity">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="simple">Simple</SelectItem>
                    <SelectItem value="balanced">Balanced</SelectItem>
                    <SelectItem value="advanced">Advanced</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground">
                  Choose the default complexity level for technique suggestions
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="techniques" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Preferred Techniques</CardTitle>
              <CardDescription>
                Select your favorite prompt engineering techniques
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 gap-4">
                {AVAILABLE_TECHNIQUES.map((technique) => (
                  <div
                    key={technique.id}
                    className="flex items-start space-x-3 p-3 rounded-lg border hover:bg-accent/50 transition-colors"
                  >
                    <Checkbox
                      id={technique.id}
                      checked={formData.preferredTechniques.includes(technique.id)}
                      onCheckedChange={() => handleTechniqueToggle(technique.id)}
                    />
                    <div className="flex-1 space-y-1">
                      <Label 
                        htmlFor={technique.id} 
                        className="font-medium cursor-pointer"
                      >
                        {technique.name}
                      </Label>
                      <p className="text-sm text-muted-foreground">
                        {technique.description}
                      </p>
                    </div>
                    {formData.preferredTechniques.includes(technique.id) && (
                      <Badge variant="secondary">Preferred</Badge>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="appearance" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Appearance Settings</CardTitle>
              <CardDescription>
                Customize the look and feel of the application
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="theme">Theme</Label>
                <Select
                  value={formData.theme}
                  onValueChange={(value) => 
                    setFormData(prev => ({ ...prev, theme: value as 'light' | 'dark' | 'system' }))
                  }
                >
                  <SelectTrigger id="theme">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">Light</SelectItem>
                    <SelectItem value="dark">Dark</SelectItem>
                    <SelectItem value="system">System</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground">
                  Choose your preferred color theme
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="language">Language</Label>
                <Select
                  value={formData.uiLanguage}
                  onValueChange={(value) => 
                    setFormData(prev => ({ ...prev, uiLanguage: value }))
                  }
                >
                  <SelectTrigger id="language">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="es">Español</SelectItem>
                    <SelectItem value="fr">Français</SelectItem>
                    <SelectItem value="de">Deutsch</SelectItem>
                    <SelectItem value="ja">日本語</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground">
                  Select your preferred language
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
              <CardDescription>
                Manage how you receive updates and notifications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="email-notifications">Email notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Receive updates about new features and improvements
                  </p>
                </div>
                <Switch
                  id="email-notifications"
                  checked={formData.emailNotifications}
                  onCheckedChange={(checked) => 
                    setFormData(prev => ({ ...prev, emailNotifications: checked }))
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="analytics">Analytics opt-in</Label>
                  <p className="text-sm text-muted-foreground">
                    Help us improve by sharing anonymous usage data
                  </p>
                </div>
                <Switch
                  id="analytics"
                  checked={formData.analyticsOptIn}
                  onCheckedChange={(checked) => 
                    setFormData(prev => ({ ...prev, analyticsOptIn: checked }))
                  }
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="mt-8 flex justify-end">
        <Button 
          onClick={handleSave} 
          disabled={saving}
          className="min-w-[120px]"
        >
          {saving ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="mr-2 h-4 w-4" />
              Save Changes
            </>
          )}
        </Button>
      </div>
    </div>
  )
}