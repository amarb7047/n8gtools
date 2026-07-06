import { initializeApp } from "firebase/app";
import { getDatabase, ref, set, onValue, get, update } from "firebase/database";

const firebaseConfig = {
  apiKey: "AIzaSyB2GL5cvc3uAeDMVevO1M8mAJ0VygMkMjQ",
  authDomain: "n8-g-tools.firebaseapp.com",
  projectId: "n8-g-tools",
  storageBucket: "n8-g-tools.firebasestorage.app",
  messagingSenderId: "1019628840739",
  appId: "1:1019628840739:web:e068fd908ee61baa990e96",
  measurementId: "G-C9LC3L8YB3",
  databaseURL: "https://n8-g-tools-default-rtdb.asia-southeast1.firebasedatabase.app"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const db = getDatabase(app);
export { ref, set, onValue, get, update };
