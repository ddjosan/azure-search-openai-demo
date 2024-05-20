import { Delete24Regular } from "@fluentui/react-icons";
import { Button, Tooltip } from "@fluentui/react-components";

import styles from "./ClearChatButton.module.css";

interface Props {
    className?: string;
    onClick: () => void;
    disabled?: boolean;
}

export const ClearChatButton = ({ className, disabled, onClick }: Props) => {
    return (
        <div className={`${styles.container} ${className ?? ""}`}>
            <Tooltip content="Clear Chat" relationship="description">
                <Button icon={<Delete24Regular />} disabled={disabled} onClick={onClick}></Button>
            </Tooltip>
        </div>
    );
};