package auth

import (
	"crypto/rand"
	"math/big"
)


// GenerateVerificationCode generates a 6-digit verification code
func GenerateVerificationCode() string {
	const digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
	code := make([]byte, 6)
	
	for i := range code {
		n, _ := rand.Int(rand.Reader, big.NewInt(int64(len(digits))))
		code[i] = digits[n.Int64()]
	}
	
	return string(code)
}