export default function SettingsPage() {
    return (
        <div className="page-container">
            <h1>Settings</h1>
            
            <div className="settings-sections">
                <section className="settings-section">
                    <h2>Account</h2>
                    <div className="settings-placeholder">
                        <p>Account management features coming soon</p>
                    </div>
                </section>
                
                <section className="settings-section">
                    <h2>Display Preferences</h2>
                    <div className="settings-placeholder">
                        <p>UI scaling options coming soon</p>
                        <p>Color theme selection coming soon</p>
                    </div>
                </section>
                
                <section className="settings-section">
                    <h2>Notifications</h2>
                    <div className="settings-placeholder">
                        <p>Email and push notification preferences coming soon</p>
                    </div>
                </section>
            </div>
        </div>
    );
}
