package main

import (
    "fmt"
    "golang.org/x/crypto/bcrypt"
)

func main() {
    password := []byte("Test123\!@#")
    
    // Generate a hash with Go bcrypt
    newHash, _ := bcrypt.GenerateFromPassword(password, 10)
    fmt.Printf("Go generated hash: %s\n", newHash)
}