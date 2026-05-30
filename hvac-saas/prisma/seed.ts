import { PrismaClient } from '@prisma/client'
import { hash } from 'bcryptjs'

const prisma = new PrismaClient()

async function main() {
  console.log('Seeding database...')

  // Create demo HVAC company
  const company = await prisma.company.upsert({
    where: { slug: 'cool-air-pros' },
    update: {},
    create: {
      name: 'Cool Air Pros',
      slug: 'cool-air-pros',
      phone: '(512) 555-0100',
      email: 'info@coolairpros.com',
      website: 'https://coolairpros.com',
      services: [
        'AC Repair',
        'Furnace Repair',
        'HVAC Installation',
        'Emergency Service',
        'Maintenance',
        'Indoor Air Quality',
      ],
      serviceArea: ['Austin', 'Round Rock', 'Cedar Park', 'Pflugerville', 'Georgetown'],
      businessHours: {
        mon: '8am-6pm',
        tue: '8am-6pm',
        wed: '8am-6pm',
        thu: '8am-6pm',
        fri: '8am-6pm',
        sat: '9am-4pm',
        sun: 'Emergency Only',
      },
      averageTicket: 850,
      monthlyFee: 1000,
      isActive: true,
    },
  })

  console.log(`Company created: ${company.name} (/${company.slug})`)

  // Create super admin
  const adminPassword = await hash(process.env.SUPER_ADMIN_PASSWORD || 'admin123', 12)
  const admin = await prisma.user.upsert({
    where: { email: process.env.SUPER_ADMIN_EMAIL || 'admin@hvacpro.com' },
    update: {},
    create: {
      email: process.env.SUPER_ADMIN_EMAIL || 'admin@hvacpro.com',
      name: 'Super Admin',
      passwordHash: adminPassword,
      role: 'SUPER_ADMIN',
    },
  })

  console.log(`Super admin created: ${admin.email}`)

  // Create company admin
  const companyPassword = await hash('company123', 12)
  const companyUser = await prisma.user.upsert({
    where: { email: 'owner@coolairpros.com' },
    update: {},
    create: {
      email: 'owner@coolairpros.com',
      name: 'Mike Johnson',
      passwordHash: companyPassword,
      role: 'COMPANY_ADMIN',
      companyId: company.id,
    },
  })

  console.log(`Company admin created: ${companyUser.email}`)

  // Create sample leads
  const leads = await Promise.all([
    prisma.lead.create({
      data: {
        companyId: company.id,
        name: 'Sarah Martinez',
        phone: '(512) 555-0201',
        email: 'sarah.m@email.com',
        service: 'AC Repair',
        urgency: 'HIGH',
        city: 'Austin',
        notes: 'AC stopped working, house is 85F, have 2 kids',
        source: 'WEBSITE',
        status: 'WON',
        estimatedValue: 850,
      },
    }),
    prisma.lead.create({
      data: {
        companyId: company.id,
        name: 'Tom Wilson',
        phone: '(512) 555-0202',
        service: 'Furnace Repair',
        urgency: 'EMERGENCY',
        city: 'Round Rock',
        notes: 'Furnace making banging noise, smells like gas',
        source: 'MISSED_CALL',
        status: 'CONTACTED',
        estimatedValue: 650,
      },
    }),
    prisma.lead.create({
      data: {
        companyId: company.id,
        name: 'Jennifer Lee',
        phone: '(512) 555-0203',
        email: 'jlee@email.com',
        service: 'HVAC Installation',
        urgency: 'NORMAL',
        city: 'Cedar Park',
        notes: 'Looking to replace old unit, house is 2200 sqft',
        source: 'CHATBOT',
        status: 'BOOKED',
        estimatedValue: 4500,
      },
    }),
    prisma.lead.create({
      data: {
        companyId: company.id,
        name: 'Robert Chen',
        phone: '(512) 555-0204',
        service: 'Maintenance',
        urgency: 'LOW',
        city: 'Pflugerville',
        source: 'WEBSITE',
        status: 'NEW',
        estimatedValue: 150,
      },
    }),
    prisma.lead.create({
      data: {
        companyId: company.id,
        name: 'Maria Garcia',
        phone: '(512) 555-0205',
        service: 'AC Repair',
        urgency: 'HIGH',
        city: 'Austin',
        source: 'MISSED_CALL',
        status: 'WON',
        estimatedValue: 750,
      },
    }),
  ])

  console.log(`Created ${leads.length} sample leads`)

  // Create sample appointment
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  tomorrow.setHours(10, 0, 0, 0)

  await prisma.appointment.create({
    data: {
      companyId: company.id,
      leadId: leads[2].id,
      customerName: 'Jennifer Lee',
      customerPhone: '(512) 555-0203',
      customerEmail: 'jlee@email.com',
      service: 'HVAC Installation Estimate',
      address: '456 Oak Lane, Cedar Park, TX 78613',
      scheduledAt: tomorrow,
      duration: 90,
      status: 'CONFIRMED',
      notes: 'New system quote for 2200 sqft home',
    },
  })

  console.log('Sample appointment created')
  console.log('\nSeed complete!')
  console.log('   Landing page: http://localhost:3000/cool-air-pros')
  console.log('   Admin login:  http://localhost:3000/login')
  console.log('   Admin email:  admin@hvacpro.com')
  console.log('   Admin pass:   admin123 (or your SUPER_ADMIN_PASSWORD env var)')
}

main()
  .catch(e => { console.error(e); process.exit(1) })
  .finally(() => prisma.$disconnect())
