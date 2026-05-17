export default function Privacy() {
  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '40px 20px', color: '#e0e0f0' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '8px' }}>Privacy Policy</h1>
      <p style={{ color: '#8080a0', fontSize: '14px', marginBottom: '32px' }}>Last updated: May 2026</p>

      <section style={{ marginBottom: '32px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '12px' }}>Data We Collect</h2>
        <p>We collect candidate profiles, assessment responses, interview feedback, and usage analytics to operate the Knowledge Factory hiring platform.</p>
      </section>

      <section style={{ marginBottom: '32px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '12px' }}>How We Use It</h2>
        <p>Data is used to generate interview questions, evaluate candidates, track hiring pipeline progress, and improve our AI models. We do not sell personal data to third parties.</p>
      </section>

      <section style={{ marginBottom: '32px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '12px' }}>Data Retention</h2>
        <p>Assessment logs and interview data are retained for 2 years after the last activity. You may request deletion of your account and all associated data by contacting support.</p>
      </section>

      <section style={{ marginBottom: '32px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '12px' }}>Cookies</h2>
        <p>We use essential cookies for authentication and preference storage. Analytics cookies are optional and can be declined.</p>
      </section>

      <section style={{ marginBottom: '32px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '12px' }}>Contact</h2>
        <p>Email: <a href="mailto:shalem@knowledge-factory.com" style={{ color: '#8b5cf6' }}>shalem@knowledge-factory.com</a></p>
      </section>
    </div>
  );
}