const http = require('http');

function testLogin() {
  const loginData = JSON.stringify({
    email_or_username: "e2etest@example.com",
    password: "Test123!@#",
    remember_me: false
  });

  const options = {
    hostname: 'localhost',
    port: 80,
    path: '/api/v1/auth/login',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': loginData.length,
      'Origin': 'http://localhost:3000'
    }
  };

  const req = http.request(options, (res) => {
    console.log('Status:', res.statusCode);
    console.log('\nAll headers:');
    console.log(res.headers);
    
    console.log('\nSet-Cookie headers:');
    const setCookies = res.headers['set-cookie'];
    if (setCookies) {
      setCookies.forEach((cookie, index) => {
        console.log(`Cookie ${index + 1}:`, cookie);
      });
    } else {
      console.log('No Set-Cookie headers found');
    }

    let data = '';
    res.on('data', (chunk) => {
      data += chunk;
    });

    res.on('end', () => {
      console.log('\nResponse body:', data);
    });
  });

  req.on('error', (error) => {
    console.error('Error:', error);
  });

  req.write(loginData);
  req.end();
}

testLogin();