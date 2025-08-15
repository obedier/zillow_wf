import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/config/database';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const jobId = parseInt(id);

    if (isNaN(jobId)) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'Invalid job ID' 
        },
        { status: 400 }
      );
    }

    const job = await prisma.extractionJob.findUnique({
      where: { id: jobId }
    });

    if (!job) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'Extraction job not found' 
        },
        { status: 404 }
      );
    }

    return NextResponse.json({
      success: true,
      data: job
    });

  } catch (error) {
    console.error('Error fetching extraction job:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to fetch extraction job',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const jobId = parseInt(id);
    const body = await request.json();

    if (isNaN(jobId)) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'Invalid job ID' 
        },
        { status: 400 }
      );
    }

    // Update the extraction job
    const updatedJob = await prisma.extractionJob.update({
      where: { id: jobId },
      data: {
        ...body,
        updatedAt: new Date()
      }
    });

    return NextResponse.json({
      success: true,
      data: updatedJob
    });

  } catch (error) {
    console.error('Error updating extraction job:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to update extraction job',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const jobId = parseInt(id);

    if (isNaN(jobId)) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'Invalid job ID' 
        },
        { status: 400 }
      );
    }

    // Delete the extraction job
    await prisma.extractionJob.delete({
      where: { id: jobId }
    });

    return NextResponse.json({
      success: true,
      message: 'Extraction job deleted successfully'
    });

  } catch (error) {
    console.error('Error deleting extraction job:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to delete extraction job',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}
