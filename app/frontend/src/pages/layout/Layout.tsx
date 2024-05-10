import { Outlet, NavLink, Link } from "react-router-dom";

import github from "../../assets/github.svg";
import logo from "../../assets/logo.png";
import undplogo from "../../assets/undp-logo-blue.png"

import styles from "./Layout.module.css";

import { useLogin } from "../../authConfig";

import { LoginButton } from "../../components/LoginButton";

const Layout = () => {
    return (
        <div className={styles.layout}>
            <header className={styles.header} role={"banner"}>
                <div className={styles.headerContainer}>
                    <div className={styles.headerLogoWrapper}>
                        <img
                            src={logo}
                            alt="UNDP GPT RS"
                            width="52px"
                            height="52px"
                        />
                        <div className={styles.headerTitleContainer}>
                            <span>UNDP Serbia</span>
                            <ul className={styles.headerDescription}>
                                <li>842 shearchable documents</li>
                                <li>1.48 Gb index data</li>
                            </ul>
                        </div>
                    </div>
                    <div>
                        <img
                            src={undplogo}
                            alt="UNDP Logo"
                            height={60}
                        />
                    </div>
                    {useLogin && <LoginButton />}
                </div>
            </header>

            <Outlet />
        </div>
    );
};

export default Layout;
