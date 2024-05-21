import { Example } from "./Example";
import example1Img from "../../assets/example1.png";
import example2Img from "../../assets/example2.png";
import example3Img from "../../assets/example3.png";
import styles from "./Example.module.css";

interface ExampleC {
    title: string,
    text: string,
    value: string,
    icon: string
}
const DEFAULT_EXAMPLES: ExampleC[] = [
    {
        title:'',
        text: '',
        value: 'Help me understand the key principles of the portfolio approach.',
        icon: example1Img
    },
    {
        title:'',
        text: '',
        value: 'Guide me through the process of preparing a portfolio policy document.',
        icon: example2Img
    },
    {
        title:'',
        text: '',
        value: "Analyze my current portfolio and provide recommendations for improvement.",
        icon: example3Img
    }
];

interface Props {
    onExampleClicked: (value: string) => void;
    useGPT4V?: boolean;
}

export const ExampleList = ({ onExampleClicked, useGPT4V }: Props) => {
    return (
        <div className={styles.examplesNavList}>
            {DEFAULT_EXAMPLES.map((question, i) => (
                <Example key={i} title={question.title} text={question.text} value={question.value} icon={question.icon} onClick={onExampleClicked} />
           ))}
        </div>
    );
};
