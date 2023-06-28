import { Outlet, NavLink, Link } from "react-router-dom";
import telkomsigmaLogo from "./logotelkomsigma.png";
import azuredanopenaiLogo from "./logoazuredanopenai.png";

import github from "../../assets/github.svg";

import styles from "./Layout.module.css";

const Layout = () => {
    return (
        <div className={styles.layout}>
            <header className={styles.header} role={"banner"}>
                <div className={styles.headerContainer}>
                    <Link to="/" className={styles.headerTitleContainer}>
                        <img src={telkomsigmaLogo} alt="Telkomsigma Logo" className={styles.headerLogo} />
                    </Link>

                    <nav>
                        <ul className={styles.headerNavList}>
                            <li>
                                <NavLink to="/" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                    ChatGPT
                                </NavLink>
                            </li>
                            <li className={styles.headerNavLeftMargin}>
                                <NavLink to="/qa" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                    Internal Data
                                </NavLink>
                            </li>
                        </ul>
                    </nav>
                    <img src={azuredanopenaiLogo} alt="Azure Logo" className={styles.headerLogo} />
                </div>
            </header>

            <Outlet />
        </div>
    );
};

export default Layout;
