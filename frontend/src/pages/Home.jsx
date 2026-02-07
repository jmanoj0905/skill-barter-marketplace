import { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores';
import { Button, Card } from '../components/common';

function Home() {
  const { isAuthenticated } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    // Redirect to dashboard if already authenticated
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  return (
    <div style={{ minHeight: '100vh' }}>
      {/* Hero Section */}
      <div style={{ textAlign: 'center', padding: '4rem 1rem', maxWidth: '800px', margin: '0 auto' }}>
        <h1 style={{ fontSize: '3rem', fontWeight: 'bold', marginBottom: '1rem' }}>
          SkillBarter
        </h1>
        <p style={{ fontSize: '1.25rem', color: '#666666', marginBottom: '2rem' }}>
          Exchange skills with others. Learn what you want by teaching what you know.
        </p>
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
          {isAuthenticated ? (
            <Link to="/dashboard" style={{ textDecoration: 'none' }}>
              <Button size="lg">Go to Dashboard</Button>
            </Link>
          ) : (
            <>
              <Link to="/register" style={{ textDecoration: 'none' }}>
                <Button size="lg">Get Started</Button>
              </Link>
              <Link to="/login" style={{ textDecoration: 'none' }}>
                <Button variant="secondary" size="lg">Sign In</Button>
              </Link>
            </>
          )}
        </div>
      </div>

      {/* Features Section */}
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 1rem 4rem' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '2rem' }}>How It Works</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem' }}>
          <Card style={{ padding: '2rem', textAlign: 'center' }}>
            <div style={{ width: '64px', height: '64px', border: '1px solid #000', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem', fontSize: '1.5rem' }}>
              📚
            </div>
            <h3 style={{ marginBottom: '0.5rem' }}>Share Your Skills</h3>
            <p style={{ color: '#666666', margin: 0 }}>
              List the skills you can teach and the skills you want to learn.
            </p>
          </Card>

          <Card style={{ padding: '2rem', textAlign: 'center' }}>
            <div style={{ width: '64px', height: '64px', border: '1px solid #000', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem', fontSize: '1.5rem' }}>
              🔄
            </div>
            <h3 style={{ marginBottom: '0.5rem' }}>Find Matches</h3>
            <p style={{ color: '#666666', margin: 0 }}>
              Our algorithm finds people who can teach what you want to learn.
            </p>
          </Card>

          <Card style={{ padding: '2rem', textAlign: 'center' }}>
            <div style={{ width: '64px', height: '64px', border: '1px solid #000', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem', fontSize: '1.5rem' }}>
              🛡️
            </div>
            <h3 style={{ marginBottom: '0.5rem' }}>Secure Exchange</h3>
            <p style={{ color: '#666666', margin: 0 }}>
              Credit escrow system ensures both parties are committed.
            </p>
          </Card>

          <Card style={{ padding: '2rem', textAlign: 'center' }}>
            <div style={{ width: '64px', height: '64px', border: '1px solid #000', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem', fontSize: '1.5rem' }}>
              💰
            </div>
            <h3 style={{ marginBottom: '0.5rem' }}>No Money Needed</h3>
            <p style={{ color: '#666666', margin: 0 }}>
              Trade skills directly. Earn credits by teaching, spend them to learn.
            </p>
          </Card>
        </div>
      </div>

      {/* CTA Section */}
      <div style={{ backgroundColor: '#000000', color: '#ffffff', padding: '3rem 1rem', textAlign: 'center' }}>
        <div style={{ maxWidth: '600px', margin: '0 auto' }}>
          <h2 style={{ marginBottom: '1rem', color: '#ffffff' }}>Ready to start learning?</h2>
          <p style={{ color: '#cccccc', marginBottom: '2rem' }}>
            Join our community of skill sharers.
          </p>
          {!isAuthenticated && (
            <Link to="/register" style={{ textDecoration: 'none' }}>
              <Button variant="secondary" size="lg">Create Account</Button>
            </Link>
          )}
        </div>
      </div>

      {/* Footer */}
      <div style={{ padding: '2rem 1rem', textAlign: 'center', borderTop: '1px solid #eeeeee' }}>
        <h3 style={{ marginBottom: '0.5rem' }}>SkillBarter</h3>
        <p style={{ color: '#666666', margin: 0 }}>
          Exchange skills, grow together.
        </p>
      </div>
    </div>
  );
}

export default Home;
