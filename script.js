const apiURL="";
// const apiURL="https://my-loginapp-qo754edula-de.a.run.app";
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
      window.location.href = 'https://storage.googleapis.com/jim_team_client0702/train/index.html';
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

async function lineLogin() {
  window.location.href = apiURL+'/linelogin';
}

async function getLineToken(code) {
  try {
      const response = await fetch(apiURL + '/get-linetoken?linetoken='+code, {
          method: 'GET',
      });

      if (response.ok) {
          const data = await response.json();
          if (data.access_token) {
              // 將 access token 儲存到 localStorage
              localStorage.setItem('access_token', data.access_token);
              console.log('access token:', data.access_token);

              window.location.href = 'https://storage.googleapis.com/jim_team_client0702/train/index.html';
              
          } else {
              console.error('Access token not found in response');
          }
      } else {
          console.error('Failed to get access token:', response.statusText);
      }
  } catch (error) {
      console.error('Error fetching access token:', error);
  }
}

// 檢查 URL 是否包含 token 參數，如果有則執行 getToken
document.addEventListener('DOMContentLoaded', () => {
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has('linetoken')) {
      getLineToken(urlParams.get('linetoken'));
  }
});