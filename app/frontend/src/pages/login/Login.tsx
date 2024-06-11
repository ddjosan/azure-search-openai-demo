import React from 'react';
import styles from './Login.module.css';
import background from '../../assets/background.png';
import undpLogoWhite from '../../assets/undp-logo-white.png';
import logoWhite from '../../assets/logo-white.png';
import { LoginButton } from '../../components/LoginButtonUNDP';


const Login: React.FC = () => {
    return (
        <div className={styles.login}>
            <div className={styles.loginHalf} style={{ backgroundImage: `url(${background})` }}>
                <div className={styles.loginHalfContent}>
                    <img src={undpLogoWhite} alt="UNDP Logo" height={70}/>
                    <h1 style={{textAlign:'center'}}> <span>Unlock Insights with Ease: </span> 
                        <br/>
                        <span>Your UNDP Serbia Data Assistant</span>
                    </h1>
                    <div>
                        <div><b>Welcome to a simpler way to navigate UNDP Serbia's wealth of knowledge.
                        Our intelligent chatbot is designed to help you: </b></div>
                        <ul>
                            <li><b>Search Smarter:</b> Leveraging GPT-4's advanced understanding, find what you need from project documents and progress reports without the hassle.</li>
                            <li><b>Get Answers:</b> Ask complex questions and get clear, referenced responses. It's like having an expert at your fingertips.</li>
                            <li><b>Explore with Confidence:</b> Powered by Azure AI Search, our chatbot combines the best search methods for comprehensive results. </li>
                            <li><b>Engage Naturally:</b> Conversations flow easily with our Structured Chat, based on the ReAct framework, making interactions intuitive and helpful.</li>
                        </ul>  
                        <div>Discover a world of information with a tool built to make complexity simple.</div>
                    </div>
                    <img src={logoWhite} alt="Logo" height={70} style={{paddingTop:'16px'}}/>
                </div>
            </div>
            <div className={styles.loginHalf}>
                <div className={styles.loginForm}>
                    <div style={{padding:'8px'}}>The single sign-on page provides users across UNDP and our UN partner agencies with simple access to our corporate AI intelligence platform using your existing agency credentials</div>
                    <LoginButton/>
                </div>
            </div>
        </div>
    );
};

export default Login;