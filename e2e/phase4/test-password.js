const bcrypt = require('bcryptjs');

async function testPassword() {
  const password = "Test123!@#";
  
  // Generate a hash
  const hash = await bcrypt.hash(password, 10);
  console.log("Generated hash:", hash);
  
  // Test verification
  const isValid = await bcrypt.compare(password, hash);
  console.log("Password verification:", isValid);
  
  // Test with the hash from the database
  const dbHash = "$2a$10$ZxW6Tlvn6H9J6Kx.BmxCIOJ8N5EO0h6i6PWBMhGFaCLBQR6wm5Ojm";
  const isValidDb = await bcrypt.compare(password, dbHash);
  console.log("DB hash verification:", isValidDb);
}

testPassword().catch(console.error);