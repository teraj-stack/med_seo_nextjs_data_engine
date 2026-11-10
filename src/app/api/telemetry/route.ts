import { NextResponse } from 'next/server';
/** Legacy demo: no persistence. Use the authenticated, validated BM Clinic application. */
export async function POST() {
  return NextResponse.json({ok:false,error:'Legacy demonstration endpoint disabled. Use the main BM Clinic application.'},{status:410});
}
