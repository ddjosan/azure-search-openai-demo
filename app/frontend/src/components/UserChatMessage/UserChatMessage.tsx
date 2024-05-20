import styles from "./UserChatMessage.module.css";
import userImage from "../../assets/user-image.png"

interface Props {
    message: string;
}

export const UserChatMessage = ({ message }: Props) => {
    return (
        <div className={styles.container}>
            <img
                src={userImage}
                alt="User"
                height='45px'
                width='45px'
            />
            <div className={styles.message}>{message}</div>
        </div>
    );
};
