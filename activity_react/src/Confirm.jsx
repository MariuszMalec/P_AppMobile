import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";

const ConfirmContext = createContext(() => Promise.resolve(false));

export function useConfirm() {
  return useContext(ConfirmContext);
}

export function ConfirmProvider({ children }) {
  const [dialog, setDialog] = useState(null);
  const resolver = useRef(null);
  const cancelRef = useRef(null);

  const confirm = useCallback(
    (opts) =>
      new Promise((resolve) => {
        resolver.current = resolve;
        setDialog({
          title: "Czy na pewno?",
          message: "",
          confirmText: "OK",
          cancelText: "Anuluj",
          danger: false,
          ...opts,
        });
      }),
    []
  );

  const close = (result) => {
    resolver.current?.(result);
    resolver.current = null;
    setDialog(null);
  };

  useEffect(() => {
    if (!dialog) return;
    cancelRef.current?.focus();
    const onKey = (e) => {
      if (e.key === "Escape") close(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [dialog]);

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      {dialog && (
        <div className="modal-bg" onClick={() => close(false)}>
          <div
            className="modal"
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="modal-title"
            onClick={(e) => e.stopPropagation()}
          >
            <div className={"modal-icon" + (dialog.danger ? " danger" : "")}>
              {dialog.danger ? "🗑" : "❓"}
            </div>
            <h3 id="modal-title">{dialog.title}</h3>
            {dialog.message && <p className="modal-msg">{dialog.message}</p>}
            <div className="modal-actions">
              <button ref={cancelRef} className="btn" onClick={() => close(false)}>
                {dialog.cancelText}
              </button>
              <button
                className={"btn " + (dialog.danger ? "btn-danger-solid" : "primary")}
                onClick={() => close(true)}
              >
                {dialog.confirmText}
              </button>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  );
}
