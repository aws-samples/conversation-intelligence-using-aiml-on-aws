/*
 * # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * # SPDX-License-Identifier: MIT-0
 */

import '@aws-amplify/ui-react/styles.css';
import {Route, Routes} from 'react-router-dom';
import {withAuthenticator} from '@aws-amplify/ui-react';
import Home from "./routes/home";
import Dashboard from './routes/dashboard';
import Admin from './routes/admin';

function App({signOut, user}) {
    return (
        <Routes>
            <Route index element={<Home />}/>
            <Route path="/dashboard/input/:key/*" element={<Dashboard userid={user.username}/>}/>
            <Route path="/admin" element={<Admin userid={user.username}/>}/>
            <Route path="/admin/prompt/:key/*" element={<Admin userid={user.username}/>}/>
        </Routes>
    );
}

export default withAuthenticator(App);