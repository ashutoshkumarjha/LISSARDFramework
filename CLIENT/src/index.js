import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import {
    createStore
} from "redux";
import Provider from "react-redux/es/components/Provider";

import rootReducer from "./reducers";
import ThemeProvider from "@mui/material/styles/ThemeProvider";
import { createTheme } from '@mui/material/styles'
import "react-datepicker/dist/react-datepicker.css";

const store = createStore(
    rootReducer,
    window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__()
);

const appTheme = createTheme({
    overrides: {
        MuiButton: {
            root: {
                textTransform: 'none'
            }
        }
    },
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
      <Provider store = {
          store
      }>
          <ThemeProvider theme={appTheme}>
                <App />
          </ThemeProvider>
      </Provider>
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
