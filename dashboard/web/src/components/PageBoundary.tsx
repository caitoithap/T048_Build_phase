// Một trang lỗi khi vẽ thì chỉ trang đó báo lỗi; menu và các trang khác vẫn dùng được.
import { Component, type ReactNode } from "react";
import { ErrorState } from "./ui";

export class PageBoundary extends Component<{ children: ReactNode }, { error: unknown }> {
  state = { error: null as unknown };

  static getDerivedStateFromError(error: unknown) {
    return { error };
  }

  render() {
    if (this.state.error === null) return this.props.children;
    return (
      <div className="flex flex-col items-start gap-3">
        <ErrorState error={this.state.error} />
        <button
          type="button"
          onClick={() => this.setState({ error: null })}
          className="h-8 rounded-lg border border-line-strong bg-surface px-3 text-[13px] font-medium hover:bg-soft"
        >
          Vẽ lại trang
        </button>
      </div>
    );
  }
}
