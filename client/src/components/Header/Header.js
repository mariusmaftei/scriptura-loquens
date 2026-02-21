import React, { useState } from "react";
import { Link } from "react-router-dom";
import styles from "./Header.module.css";
import bibleLogo from "../../assets/images/bible-main-image.png";

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const closeMenu = () => {
    setIsMenuOpen(false);
  };

  return (
    <>
      {isMenuOpen && <div className={styles.overlay} onClick={closeMenu}></div>}
      <header className={styles.header}>
        <div className="container">
          <div className={styles.content}>
            <Link to="/" className={styles.logoLink} onClick={closeMenu}>
              <img src={bibleLogo} alt="Logo" className={styles.logoImage} />
              <h1 className={styles.logo}>Scriptura Loquens</h1>
            </Link>
            <button
              className={styles.burgerButton}
              onClick={toggleMenu}
              aria-label="Deschide meniul"
              aria-expanded={isMenuOpen}
            >
              <span className={styles.burgerLine}></span>
              <span className={styles.burgerLine}></span>
              <span className={styles.burgerLine}></span>
            </button>
            <nav
              className={`${styles.nav} ${isMenuOpen ? styles.navOpen : ""}`}
              onClick={(e) => e.stopPropagation()}
            >
              <Link to="/" className={styles.navLink} onClick={closeMenu}>
                Acasă
              </Link>
              <Link
                to="/biblioteca"
                className={styles.navLink}
                onClick={closeMenu}
              >
                Bibliotecă
              </Link>
              <Link to="/import" className={styles.navLink} onClick={closeMenu}>
                Import
              </Link>
              <Link
                to="/analizeaza"
                className={styles.navLink}
                onClick={closeMenu}
              >
                Analizează JSON
              </Link>
              <Link
                to="/post-productie"
                className={styles.navLink}
                onClick={closeMenu}
              >
                Post-producție
              </Link>
            </nav>
          </div>
        </div>
      </header>
    </>
  );
};

export default Header;
