// Main App component with routing

import { Routes, Route } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import { AuthProvider } from './context/AuthContext';
import { Navigation } from './components/Navigation';
import { Home } from './pages/Home';
import { Movies } from './pages/Movies';
import { TvShows } from './pages/TvShows';
import { Watch } from './pages/Watch';
import { Favorites } from './pages/Favorites';
import { MyList } from './pages/MyList';
import { History } from './pages/History';
import { Search } from './pages/Search';
import { Trending } from './pages/Trending';
import { Kids } from './pages/Kids';
import { Profile } from './pages/Profile';
import { Shuffle } from './pages/Shuffle';
import { Upcoming } from './pages/Upcoming';
import { Login } from './pages/auth/Login';
import { Signup } from './pages/auth/Signup';
import { VerifyOTP } from './pages/auth/VerifyOTP';
import { ForgotPassword } from './pages/auth/ForgotPassword';
import { ResetPassword } from './pages/auth/ResetPassword';

function App() {
    return (
        <AuthProvider>
            <AppProvider>
                <div className="min-h-screen bg-dark-900 overflow-x-hidden">
                    <Navigation />
                    <Routes>
                        <Route path="/" element={<Home />} />
                        <Route path="/movies" element={<Movies />} />
                        <Route path="/tv-shows" element={<TvShows />} />
                        <Route path="/kids" element={<Kids />} />
                        <Route path="/watch/:imdbId" element={<Watch />} />
                        <Route path="/favorites" element={<Favorites />} />
                        <Route path="/my-list" element={<MyList />} />
                        <Route path="/history" element={<History />} />
                        <Route path="/search" element={<Search />} />
                        <Route path="/trending" element={<Trending />} />
                        <Route path="/shuffle" element={<Shuffle />} />
                        <Route path="/upcoming" element={<Upcoming />} />
                        <Route path="/profile" element={<Profile />} />

                        {/* Auth Routes */}
                        <Route path="/login" element={<Login />} />
                        <Route path="/signup" element={<Signup />} />
                        <Route path="/verify-otp" element={<VerifyOTP />} />
                        <Route path="/forgot-password" element={<ForgotPassword />} />
                        <Route path="/reset-password" element={<ResetPassword />} />
                    </Routes>
                </div>
            </AppProvider>
        </AuthProvider>
    );
}



export default App;
