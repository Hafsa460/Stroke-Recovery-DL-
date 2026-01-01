const fileInput = document.getElementById('fileInput');
const previewBtn = document.getElementById('previewBtn');
const uploadBtn = document.getElementById('uploadBtn');
const previewArea = document.getElementById('previewArea');
const previewImg = document.getElementById('previewImg');
const fileName = document.getElementById('fileName');
const resultArea = document.getElementById('resultArea');
const errorMsg = document.getElementById('errorMsg');

let selectedFile = null;

fileInput.addEventListener('change', (e) => {
  selectedFile = e.target.files[0] || null;
  resultArea.style.display = 'none';
  errorMsg.textContent = '';
  previewArea.style.display = 'none';
  uploadBtn.disabled = true;
});

previewBtn.addEventListener('click', () => {
  if (!selectedFile) {
    errorMsg.textContent = 'Select an image first';
    return;
  }
  const url = URL.createObjectURL(selectedFile);
  previewImg.src = url;
  fileName.textContent = selectedFile.name;
  previewArea.style.display = 'block';
  uploadBtn.disabled = false;
  errorMsg.textContent = '';
});

document.getElementById('uploadForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!selectedFile) {
    errorMsg.textContent = 'Select an image first';
    return;
  }
  uploadBtn.disabled = true;
  uploadBtn.textContent = 'Processing...';
  errorMsg.textContent = '';

  const fd = new FormData();
  fd.append('image', selectedFile);

  try {
    const res = await fetch('/api/predict', { method: 'POST', body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || 'Server error');
    resultArea.style.display = 'block';
    resultArea.innerHTML = `<h4>Prediction Result:</h4>
      <p><strong>Prediction:</strong> ${data.prediction}</p>
      <p><strong>Confidence:</strong> ${Math.round((data.confidence||0)*100)}%</p>`;
  } catch (err) {
    errorMsg.textContent = err.message || 'Request failed';
  } finally {
    uploadBtn.disabled = false;
    uploadBtn.textContent = 'Upload & Get Result';
  }
});
