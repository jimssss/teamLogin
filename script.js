const apiURL=" https://my-loginapp2-qo754edula-uc.a.run.app";
document.getElementById('loginForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
  
    const response = await fetch( apiURL +'/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams({
        username: email,
        password: password
      })
    });
  
    if (response.ok) {
      const data = await response.json();
      console.log('Access token:', data.access_token);
      localStorage.setItem('access_token', data.access_token);
      // You can now use the access token to authenticate API requests
    } else {
      console.error('Login failed');
    }
  });
  
document.getElementById('registerForm').addEventListener('submit', async function(event) {
  event.preventDefault();
  const email = document.getElementById('registerEmail').value;
  const password = document.getElementById('registerPassword').value;

  const response = await fetch( apiURL + '/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      email: email,
      password: password
    })
  });

  if (response.ok) {
    console.log('User registered successfully');
    showLoginForm();
  } else {
    console.error('Registration failed');
  }
});

function showRegisterForm() {
  document.getElementById('registerFormContainer').classList.remove('hidden');
  document.getElementById('loginForm').closest('.flex').classList.add('hidden');
}

function showLoginForm() {
  document.getElementById('registerFormContainer').classList.add('hidden');
  document.getElementById('loginForm').closest('.flex').classList.remove('hidden');
}
