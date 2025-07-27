# Phase 12: Mobile & Accessibility (US-019 + US-020)

## Overview
- **User Story**: "As a mobile/disabled user, I want full access to all features"
- **Duration**: 3 days
- **Complexity**: Medium - Responsive design, WCAG compliance, touch interactions
- **Status**: ⬜ READY

## Dependencies
- **Depends On**: None (UI testing focus)
- **Enables**: Inclusive user experience
- **Can Run In Parallel With**: Any phase

## Why This Phase
- Can run in parallel
- Legal compliance (ADA/WCAG)
- Expands user base
- Improves UX for all

## Implementation Command
```bash
/sc:test e2e \
  --persona-frontend \
  --persona-qa \
  --play --magic --c7 \
  --think --validate \
  --phase-config '{
    "phase": 12,
    "name": "Mobile & Accessibility",
    "focus": ["accessibility", "mobile", "ux"],
    "stories": ["US-019", "US-020"],
    "duration": "3 days",
    "complexity": "medium",
    "compliance": "WCAG_2.1_AA"
  }' \
  --test-requirements '{
    "mobile_testing": {
      "viewports": {
        "mobile_small": {"width": 320, "height": 568, "device": "iPhone_SE"},
        "mobile_medium": {"width": 375, "height": 667, "device": "iPhone_8"},
        "mobile_large": {"width": 414, "height": 896, "device": "iPhone_11_Pro"},
        "tablet": {"width": 768, "height": 1024, "device": "iPad"},
        "desktop": {"width": 1920, "height": 1080, "device": "Desktop"}
      },
      "touch_interactions": {
        "gestures": ["tap", "swipe", "pinch", "long_press", "double_tap"],
        "targets": {"minimum_size": "44x44px", "spacing": "8px"}
      },
      "responsive_breakpoints": ["320px", "768px", "1024px", "1920px"]
    },
    "accessibility": {
      "wcag_2_1_aa": {
        "perceivable": ["alt_text", "captions", "color_contrast", "text_resize"],
        "operable": ["keyboard_access", "focus_order", "skip_links", "timing"],
        "understandable": ["labels", "errors", "consistency", "instructions"],
        "robust": ["valid_html", "aria_usage", "compatibility"]
      },
      "screen_readers": ["NVDA", "JAWS", "VoiceOver", "TalkBack"],
      "color_contrast": {
        "normal_text": "4.5:1",
        "large_text": "3:1",
        "ui_components": "3:1"
      }
    }
  }' \
  --test-patterns '{
    "mobile_patterns": {
      "viewport_testing": ["responsive_design", "orientation_change", "zoom_prevention"],
      "touch_testing": ["gesture_recognition", "target_size", "scroll_behavior"],
      "performance": ["lazy_loading", "image_optimization", "viewport_meta"]
    },
    "a11y_patterns": {
      "automated": ["axe_core", "pa11y", "lighthouse"],
      "manual": ["screen_reader_flow", "keyboard_navigation", "focus_management"],
      "validation": ["aria_attributes", "semantic_html", "landmark_regions"]
    }
  }' \
  --deliverables '{
    "test_files": [
      "us-019-mobile-experience.spec.ts",
      "us-020-accessibility.spec.ts",
      "mobile-a11y-combined.spec.ts"
    ],
    "utilities": [
      "viewport-helper.ts",
      "touch-gesture-simulator.ts",
      "accessibility-validator.ts",
      "screen-reader-helper.ts"
    ],
    "documentation": [
      "mobile-test-results.md",
      "accessibility-audit.md",
      "wcag-compliance-report.md"
    ]
  }' \
  --validation-gates '{
    "mobile": {
      "all_viewports_work": true,
      "touch_targets_accessible": true,
      "responsive_design_valid": true
    },
    "accessibility": {
      "wcag_aa_compliant": true,
      "screen_reader_compatible": true,
      "keyboard_navigable": true,
      "color_contrast_passes": true
    },
    "cross_browser": {
      "mobile": ["mobile_chrome", "mobile_safari", "samsung_browser"],
      "desktop": ["chrome", "firefox", "safari", "edge"]
    }
  }' \
  --output-dir "e2e/phase12"
```

## Success Metrics
- [ ] Works on all viewports
- [ ] WCAG 2.1 AA compliant
- [ ] Screen reader friendly
- [ ] Full keyboard access
- [ ] Touch targets ≥44px
- [ ] Color contrast passes

## Progress Tracking
- [ ] Test file created: `us-019-020-mobile-a11y.spec.ts`
- [ ] Mobile viewport helpers implemented
- [ ] Responsive breakpoint tests complete
- [ ] Touch interaction tests complete
- [ ] Accessibility scan tests complete
- [ ] Screen reader tests complete
- [ ] Keyboard navigation tests complete
- [ ] Color contrast tests complete
- [ ] Cross-device validation complete
- [ ] Documentation updated

## Test Scenarios

### Mobile Viewport Tests
```javascript
// Test viewports
- iPhone SE: 375x667
- iPhone 12: 390x844
- iPad: 768x1024
- Galaxy S21: 360x800
- Desktop: 1920x1080
```

### Responsive Breakpoints
- Mobile: 320px - 767px
- Tablet: 768px - 1023px
- Desktop: 1024px+
- Ultra-wide: 1920px+

### Touch Interaction Tests
- Tap targets (min 44x44px)
- Swipe gestures
- Pinch to zoom
- Long press actions
- Double tap
- Touch scrolling

### WCAG 2.1 AA Tests
- **Perceivable**: Alt text, captions, contrast
- **Operable**: Keyboard access, timing, navigation
- **Understandable**: Labels, errors, consistency
- **Robust**: Valid HTML, ARIA usage

### Screen Reader Tests
```javascript
// Test with multiple readers
- NVDA (Windows)
- JAWS (Windows)
- VoiceOver (macOS/iOS)
- TalkBack (Android)

// Key areas
- Navigation landmarks
- Form labels and errors
- Dynamic content updates
- Modal dialogs
- Loading states
```

### Keyboard Navigation
- Tab order logical
- Focus indicators visible
- Skip links available
- Modal trap focus
- Escape key handling
- Enter/Space activation

### Color Contrast Tests
- Normal text: 4.5:1 ratio
- Large text: 3:1 ratio
- UI components: 3:1 ratio
- Focus indicators: 3:1 ratio
- Error states: 4.5:1 ratio

## Notes & Updates

### Prerequisites
- Responsive design implemented
- ARIA labels added
- Semantic HTML used
- Touch event handlers
- Keyboard event handlers

### Accessibility Tools
```javascript
// Automated testing
import { AxeBuilder } from '@axe-core/playwright';

// Manual testing checklist
- Screen reader announcement flow
- Keyboard-only navigation
- High contrast mode
- Browser zoom 200%
- Reduced motion preferences
```

### Implementation Tips
1. Test real devices when possible
2. Use emulators for basic testing
3. Test with actual screen readers
4. Involve users with disabilities
5. Document accessibility features

### Mobile-Specific Considerations
```css
/* Touch target sizing */
.button {
  min-height: 44px;
  min-width: 44px;
}

/* Viewport meta tag */
<meta name="viewport" content="width=device-width, initial-scale=1">

/* Prevent zoom on input focus (iOS) */
input { font-size: 16px; }
```

### Common Issues
- **Small touch targets**: Increase button/link size
- **Missing labels**: Add aria-label or screen reader text
- **Low contrast**: Use color contrast analyzer
- **Keyboard traps**: Ensure all modals can be escaped
- **Missing focus indicators**: Add visible focus styles

---

*Last Updated: 2025-01-27*