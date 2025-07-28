async function registerTestUser() {
  const registerData = {
    email: "e2etest@example.com",
    username: "e2etest",
    password: "Test123!@#",
    confirm_password: "Test123!@#",
    name: "E2E Test User"
  };

  try {
    const response = await fetch('http://localhost/api/v1/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Origin': 'http://localhost:3000'
      },
      body: JSON.stringify(registerData),
      credentials: 'include'
    });

    const data = await response.json();
    console.log('Status:', response.status);
    console.log('Response:', data);

    if (response.status === 201) {
      console.log('\nRegistration successful! Now testing login...');
      
      // Test login
      const loginData = {
        email_or_username: "e2etest@example.com",
        password: "Test123!@#",
        remember_me: false
      };

      const loginResponse = await fetch('http://localhost/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Origin': 'http://localhost:3000'
        },
        body: JSON.stringify(loginData),
        credentials: 'include'
      });

      const loginResult = await loginResponse.json();
      console.log('\nLogin Status:', loginResponse.status);
      
      // Get all set-cookie headers
      const setCookieHeaders = loginResponse.headers.raw()['set-cookie'] || [];
      console.log('Set-Cookie headers:', setCookieHeaders);
      
      console.log('Login Response:', loginResult);
    }
  } catch (error) {
    console.error('Error:', error);
  }
}

registerTestUser();