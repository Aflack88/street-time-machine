import dynamic from "next/dynamic";
const ReactCompareImage = dynamic(() => import("react-compare-image"), { ssr: false });

export default function CompareSlider({ left, right, leftLabel="Now", rightLabel="Then" }) {
  return (
    <div style={{ maxWidth: 900 }}>
      <ReactCompareImage leftImage={left} rightImage={right} leftImageLabel={leftLabel} rightImageLabel={rightLabel} />
    </div>
  );
}
