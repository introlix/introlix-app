declare module 'lodash.debounce' {
  type Procedure = (...args: any[]) => any;
  interface DebouncedFunction<T extends Procedure> {
    (...args: Parameters<T>): ReturnType<T> | undefined;
    cancel(): void;
    flush(): ReturnType<T> | undefined;
  }
  function debounce<T extends Procedure>(func: T, wait?: number, options?: { leading?: boolean; trailing?: boolean; maxWait?: number }): DebouncedFunction<T>;
  export default debounce;
}