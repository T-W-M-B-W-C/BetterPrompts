package services

import (
	"bytes"
	"context"
	"fmt"
	"html/template"
	"net/smtp"
	"os"
	"strings"
	"time"

	"github.com/sirupsen/logrus"
)

// EmailService handles email sending operations
type EmailService struct {
	host     string
	port     string
	from     string
	username string
	password string
	logger   *logrus.Logger
}

// NewEmailService creates a new email service
func NewEmailService(logger *logrus.Logger) *EmailService {
	service := &EmailService{
		host:     getEnv("SMTP_HOST", "localhost"),
		port:     getEnv("SMTP_PORT", "1025"),
		from:     getEnv("SMTP_FROM", "noreply@betterprompts.com"),
		username: getEnv("SMTP_USERNAME", ""),
		password: getEnv("SMTP_PASSWORD", ""),
		logger:   logger,
	}
	
	logger.WithFields(logrus.Fields{
		"smtp_host": service.host,
		"smtp_port": service.port,
		"smtp_from": service.from,
	}).Info("Email service initialized")
	
	return service
}

// EmailData represents data for email templates
type EmailData struct {
	To              string
	Subject         string
	VerificationCode string
	VerificationLink string
	Username        string
	AppName         string
	AppURL          string
}

// SendVerificationEmail sends an email verification message
func (s *EmailService) SendVerificationEmail(ctx context.Context, to, username, code, token string) error {
	s.logger.WithFields(logrus.Fields{
		"to": to,
		"username": username,
		"code": code,
		"smtp_host": s.host,
		"smtp_port": s.port,
	}).Debug("Attempting to send verification email")
	
	appURL := getEnv("APP_URL", "http://localhost:3000")
	verificationLink := fmt.Sprintf("%s/verify-email?token=%s", appURL, token)

	data := EmailData{
		To:              to,
		Subject:         "Verify your BetterPrompts account",
		VerificationCode: code,
		VerificationLink: verificationLink,
		Username:        username,
		AppName:         "BetterPrompts",
		AppURL:          appURL,
	}

	htmlBody, err := s.renderTemplate("verification", data)
	if err != nil {
		return fmt.Errorf("failed to render email template: %w", err)
	}

	return s.sendEmail(ctx, data.To, data.Subject, htmlBody)
}

// sendEmail sends an email using SMTP
func (s *EmailService) sendEmail(ctx context.Context, to, subject, body string) error {
	// Build the email message
	msg := s.buildMessage(to, subject, body)

	// Connect to SMTP server
	addr := fmt.Sprintf("%s:%s", s.host, s.port)
	
	// For development (MailHog), we don't need authentication
	var auth smtp.Auth
	if s.username != "" && s.password != "" {
		auth = smtp.PlainAuth("", s.username, s.password, s.host)
	}

	// Send the email
	err := smtp.SendMail(addr, auth, s.from, []string{to}, []byte(msg))
	if err != nil {
		s.logger.WithError(err).WithFields(logrus.Fields{
			"to":   to,
			"from": s.from,
			"host": s.host,
			"port": s.port,
		}).Error("Failed to send email")
		return fmt.Errorf("failed to send email: %w", err)
	}

	s.logger.WithFields(logrus.Fields{
		"to":      to,
		"subject": subject,
	}).Info("Email sent successfully")

	return nil
}

// buildMessage builds the email message with headers
func (s *EmailService) buildMessage(to, subject, body string) string {
	headers := make(map[string]string)
	headers["From"] = s.from
	headers["To"] = to
	headers["Subject"] = subject
	headers["MIME-Version"] = "1.0"
	headers["Content-Type"] = "text/html; charset=\"utf-8\""
	headers["Date"] = time.Now().Format(time.RFC1123Z)

	var msg strings.Builder
	for k, v := range headers {
		msg.WriteString(fmt.Sprintf("%s: %s\r\n", k, v))
	}
	msg.WriteString("\r\n")
	msg.WriteString(body)

	return msg.String()
}

// renderTemplate renders an email template
func (s *EmailService) renderTemplate(templateName string, data EmailData) (string, error) {
	tmplStr := s.getEmailTemplate(templateName)
	
	tmpl, err := template.New(templateName).Parse(tmplStr)
	if err != nil {
		return "", fmt.Errorf("failed to parse template: %w", err)
	}

	var buf bytes.Buffer
	if err := tmpl.Execute(&buf, data); err != nil {
		return "", fmt.Errorf("failed to execute template: %w", err)
	}

	return buf.String(), nil
}

// getEmailTemplate returns the HTML template for emails
func (s *EmailService) getEmailTemplate(templateName string) string {
	switch templateName {
	case "verification":
		return `<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{.Subject}}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 600px;
            margin: 40px auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }
        .content {
            padding: 40px 30px;
        }
        .verification-code {
            background-color: #f8f9fa;
            border: 2px dashed #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin: 30px 0;
            text-align: center;
        }
        .code {
            font-size: 32px;
            font-weight: bold;
            letter-spacing: 4px;
            color: #495057;
            font-family: 'Courier New', monospace;
        }
        .button {
            display: inline-block;
            padding: 12px 30px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 500;
            margin: 20px 0;
        }
        .button:hover {
            background: #5a67d8;
        }
        .footer {
            background-color: #f8f9fa;
            padding: 30px;
            text-align: center;
            font-size: 14px;
            color: #6c757d;
        }
        .footer a {
            color: #667eea;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{.AppName}}</h1>
            <p style="margin-top: 10px; opacity: 0.9;">Verify Your Email Address</p>
        </div>
        
        <div class="content">
            <p>Hi {{.Username}},</p>
            
            <p>Welcome to {{.AppName}}! We're excited to have you on board. To complete your registration, please verify your email address.</p>
            
            <div class="verification-code">
                <p style="margin: 0 0 10px 0; color: #6c757d;">Your verification code is:</p>
                <div class="code">{{.VerificationCode}}</div>
            </div>
            
            <p style="text-align: center;">Or click the button below to verify your email:</p>
            
            <div style="text-align: center;">
                <a href="{{.VerificationLink}}" class="button">Verify Email Address</a>
            </div>
            
            <p style="margin-top: 30px; color: #6c757d; font-size: 14px;">
                If you didn't create an account with {{.AppName}}, you can safely ignore this email.
            </p>
        </div>
        
        <div class="footer">
            <p>This email was sent by {{.AppName}}</p>
            <p>
                <a href="{{.AppURL}}">Visit our website</a> | 
                <a href="{{.AppURL}}/privacy">Privacy Policy</a> | 
                <a href="{{.AppURL}}/terms">Terms of Service</a>
            </p>
        </div>
    </div>
</body>
</html>`
	default:
		return ""
	}
}

// getEnv gets an environment variable with a default value
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}