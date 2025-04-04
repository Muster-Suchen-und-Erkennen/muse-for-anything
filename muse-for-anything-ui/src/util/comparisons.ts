/**
 * Check if two (JSON serializable) values are the same using a deep comparison.
 *
 * @param a value a
 * @param b value b
 * @returns if value a is the same as value b
 */
export function deepEqual(a, b): boolean {
    // check for primitive or identity equality
    if (a === b) {
        return true;
    }

    // check arrays recursively
    if (Array.isArray(a) !== Array.isArray(b)) {
        return false; // different types
    }
    if (Array.isArray(a) && Array.isArray(b)) {
        if (a.length !== b.length) {
            return false;  // length mismatch
        }
        return a.every((vA, i) => deepEqual(vA, b[i]));
    }

    // check objects recursively
    if (typeof a !== typeof b) {
        return false; // different types
    }
    if (typeof a === "object" && typeof b === "object") {
        const aKeys = Object.keys(a).filter(k => a.hasOwnProperty(k));
        const bKeys = Object.keys(b).filter(k => b.hasOwnProperty(k));
        if (aKeys.length !== bKeys.length) {
            return false;  // key size mismatch
        }
        return aKeys.every(k => b.hasOwnProperty(k) && deepEqual(a[k], b[k]));
    }

    // assume unequal by default
    return false;
}
