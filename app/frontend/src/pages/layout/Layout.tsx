import { Outlet, NavLink, Link, useNavigate } from "react-router-dom";

import github from "../../assets/github.svg";
import logo from "../../assets/logo.png";
import undplogo from "../../assets/undp-logo-blue.png";

import styles from "./Layout.module.css";

import { appServicesToken, useLogin } from "../../authConfig";

import { LoginButton } from "../../components/LoginButton";
import { UserProfile } from "../../components/UserProfile";

import { useMsal } from "@azure/msal-react";
import { useEffect } from "react";

const Layout = () => {
    const { instance } = useMsal();
    const activeAccount = instance.getActiveAccount();
    const isLoggedIn = (activeAccount || appServicesToken) != null;
    const navigate = useNavigate();

    useEffect(() => {
        const isLoggedIn = (activeAccount || appServicesToken) != null;
        if (!isLoggedIn) {
            navigate("/login");
        }
    }, [activeAccount, appServicesToken]);

    return (
        <div className={styles.layout}>
            <header className={styles.header} role={"banner"}>
                <div className={styles.headerContainer}>
                    <div className={styles.headerLogoWrapper}>
                        {/* <img src={logo} alt="UNDP GPT RS" width="52px" height="52px" /> */}
                        <img src={undplogo} alt="UNDP Logo" height={60} />
                        <div className={styles.headerTitleContainer}>
                            <span>UNDP Serbia</span>
                            <ul className={styles.headerDescription}>
                                <li>842 shearchable documents</li>
                                <li>1.48 Gb index data</li>
                            </ul>
                        </div>
                    </div>
                    <div>
                        {
                            <UserProfile />
                            /* <img
                            src={undplogo}
                            alt="UNDP Logo"
                            height={60}
                        /> */
                        }
                    </div>
                    {/* {useLogin && <LoginButton />} */}
                </div>
            </header>

            <Outlet />
        </div>
    );
};

export default Layout;
