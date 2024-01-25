/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import { useState } from 'react';

 const saveLocalStorage = (key, value) => {
  localStorage.setItem(key, JSON.stringify(value));
}

 const loadLocalStorage = (key) => {
  console.log('load local storage: ', key);
  const value = localStorage.getItem(key);
  try {
    return value && JSON.parse(value);
  } catch (e) {
    console.warn(
      `⚠️ The ${key} value that is stored in localStorage is incorrect. Try to remove the value ${key} from localStorage and reload the page`
    );
    return undefined;
  }
}

 function useLocalStorage(key, defaultValue) {
  const [value, setValue] = useState(() => loadLocalStorage(key) ?? defaultValue);
  
  function handleValueChange(newValue) {
    setValue(newValue);
    saveLocalStorage(key, newValue);
  }

  return [value, handleValueChange];
}

const AppLocalStorage = { saveLocalStorage, loadLocalStorage , useLocalStorage};
export default AppLocalStorage;