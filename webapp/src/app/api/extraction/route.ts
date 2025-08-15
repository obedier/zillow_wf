import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/config/database';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { urls, userId = 'default' } = body;

    if (!urls || !Array.isArray(urls) || urls.length === 0) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'URLs array is required and must not be empty' 
        },
        { status: 400 }
      );
    }

    // Create a new extraction job
    const extractionJob = await prisma.extractionJob.create({
      data: {
        urls,
        totalUrls: urls.length,
        status: 'pending',
        progress: 0,
        processedUrls: 0,
        errorCount: 0,
        createdAt: new Date(),
      }
    });

    // TODO: In Phase 4, this will trigger the actual Python extraction script
    // For now, we'll simulate the job starting
    console.log(`Starting extraction job ${extractionJob.id} with ${urls.length} URLs`);

    // Simulate job progression (remove this in production)
    setTimeout(async () => {
      await prisma.extractionJob.update({
        where: { id: extractionJob.id },
        data: { 
          status: 'running',
          startedAt: new Date(),
          progress: 10
        }
      });
    }, 1000);

    return NextResponse.json({
      success: true,
      data: {
        jobId: extractionJob.id,
        message: 'Extraction job started successfully',
        job: extractionJob
      }
    });

  } catch (error) {
    console.error('Error starting extraction job:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to start extraction job',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '10');
    const offset = (page - 1) * limit;

    // Get total count
    const totalCount = await prisma.extractionJob.count();

    // Get extraction jobs with pagination
    const jobs = await prisma.extractionJob.findMany({
      orderBy: { createdAt: 'desc' },
      skip: offset,
      take: limit,
    });

    return NextResponse.json({
      success: true,
      data: {
        jobs,
        pagination: {
          page,
          limit,
          total: totalCount,
          totalPages: Math.ceil(totalCount / limit),
          hasNext: page < Math.ceil(totalCount / limit),
          hasPrev: page > 1,
        }
      }
    });

  } catch (error) {
    console.error('Error fetching extraction jobs:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to fetch extraction jobs',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}
