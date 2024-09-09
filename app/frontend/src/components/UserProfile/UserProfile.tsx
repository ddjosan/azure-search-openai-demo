import * as React from "react";
import { Avatar, Menu, MenuItem, MenuPopover, MenuTrigger, MenuList } from "@fluentui/react-components";
import { SignOutRegular } from "@fluentui/react-icons"; // Import the sign-out icon
import { useMsal } from "@azure/msal-react";
import { getRedirectUri, loginRequest } from "../../authConfig";
import { appServicesToken, appServicesLogout } from "../../authConfig";

export const UserProfile = () => {
    const { instance } = useMsal();
    const activeAccount = instance.getActiveAccount();
    const isLoggedIn = (activeAccount || appServicesToken) != null;

    const handleLogoutPopup = () => {
        if (activeAccount) {
            instance
                .logoutPopup({
                    mainWindowRedirectUri: "/", // redirects the top level app after logout
                    account: instance.getActiveAccount()
                })
                .catch(error => console.log(error));
        } else {
            appServicesLogout();
        }
    };

    const avatarStyles = {
        borderRadius: "50%",
        border: "2px solid lightgray", // Light border around avatar
        backgroundColor: "#9AC0FF",
        cursor: "pointer",
        display: "inline-block"
    };

    const menuListStyles = {
        backgroundColor: "white", // White background for menu list
        boxShadow: "0px 4px 12px rgba(0, 0, 0, 0.1)" // Optional shadow for better appearance
    };

    const logoutText = `Logout\n${activeAccount?.name ?? appServicesToken?.user_claims?.preferred_username}`;

    return (
        <Menu>
            <MenuTrigger>
                <div style={avatarStyles}>
                    <Avatar name={activeAccount?.name ?? appServicesToken?.user_claims?.preferred_username} size={40} />
                </div>
            </MenuTrigger>

            <MenuPopover>
                <MenuList style={menuListStyles}>
                    <MenuItem icon={<SignOutRegular />} onClick={handleLogoutPopup}>
                        Sign Out
                    </MenuItem>
                </MenuList>
            </MenuPopover>
        </Menu>
    );
};
