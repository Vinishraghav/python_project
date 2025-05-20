// static/js/firebase-config.js
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyCXRxzfXOxAIlkBxEi_HQmrhsvbxDq2ito",
  authDomain: "tourvanbooking.firebaseapp.com",
  projectId: "tourvanbooking",
  storageBucket: "tourvanbooking.firebasestorage.app",
  messagingSenderId: "486666007493",
  appId: "1:486666007493:web:d937abe82cf8aff5ed91ac",
  measurementId: "G-RBJ4EZPER3",
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
