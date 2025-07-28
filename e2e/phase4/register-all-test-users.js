const testUsers = [
  {
    email: "test@example.com",
    username: "testuser",
    password: "Test123456!",
    confirm_password: "Test123456!",
    name: "Test User"
  },
  {
    email: "power@example.com",
    username: "poweruser",
    password: "Power123456!",
    confirm_password: "Power123456!",
    name: "Power User"
  },
  {
    email: "new@example.com",
    username: "newuser",
    password: "New123456!",
    confirm_password: "New123456!",
    name: "New User"
  }
];

async function registerUser(userData) {
  try {
    const response = await fetch('http://localhost/api/v1/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Origin': 'http://localhost:3000'
      },
      body: JSON.stringify(userData),
      credentials: 'include'
    });

    const data = await response.json();
    if (response.status === 201) {
      console.log(`✅ Successfully registered ${userData.email}`);
    } else if (response.status === 409) {
      console.log(`ℹ️  User ${userData.email} already exists`);
    } else {
      console.log(`❌ Failed to register ${userData.email}:`, data);
    }
  } catch (error) {
    console.error(`❌ Error registering ${userData.email}:`, error.message);
  }
}

async function registerAllTestUsers() {
  console.log('Registering test users...\n');
  
  for (const user of testUsers) {
    await registerUser(user);
  }
  
  console.log('\nDone!');
}

registerAllTestUsers();