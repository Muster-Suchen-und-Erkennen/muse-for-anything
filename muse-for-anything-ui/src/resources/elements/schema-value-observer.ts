export interface SchemaValueObserver {
    onValueChanged: (key: string, newValue, oldValue) => void;
    onValidityChanged?: (key: string, newValue, oldValue) => void;
}
