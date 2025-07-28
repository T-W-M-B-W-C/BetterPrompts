async function testLogin() {
  const loginData = {
    email_or_username: "admin@betterprompts.com",
    password: "admin123",
    remember_me: false
  };

  try {
    const response = await fetch('http://localhost/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Origin': 'http://localhost:3000'
      },
      body: JSON.stringify(loginData),
      credentials: 'include'
    });

    const data = await response.json();
    console.log('Status:', response.status);
    console.log('Headers:', Object.fromEntries(response.headers));
    console.log('Response:', data);

    if (response.headers.get('set-cookie')) {
      console.log('Cookies set:', response.headers.get('set-cookie'));
    }
  } catch (error) {
    console.error('Error:', error);
  }
}

testLogin();