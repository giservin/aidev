import { Example } from "./Example";

import styles from "./Example.module.css";

export type ExampleModel = {
    text: string;
    value: string;
};

const EXAMPLES: ExampleModel[] = [
    {
        text: "Tampilkan informasi PT. Pertamina",
        value: "Tampilkan informasi PT. Pertamina"
    },
    { text: "Tampilkan alamat PT. Pertamina", value: "Tampilkan alamat PT. Pertamina" },
    { text: "Tampilkan visi dan misi PT. Pertamina", value: "Tampilkan visi dan misi PT. Pertamina" }
];

interface Props {
    onExampleClicked: (value: string) => void;
}

export const ExampleList = ({ onExampleClicked }: Props) => {
    return (
        <ul className={styles.examplesNavList}>
            {EXAMPLES.map((x, i) => (
                <li key={i}>
                    <Example text={x.text} value={x.value} onClick={onExampleClicked} />
                </li>
            ))}
        </ul>
    );
};
